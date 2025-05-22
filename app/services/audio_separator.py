import os
import logging
import uuid
from typing import Dict, Optional, List, Tuple, Callable
import torch

logger = logging.getLogger(__name__)

class AudioSeparator:
    """Service for separating audio tracks using demucs models"""
    
    def __init__(self, config):
        self.config = config
        self.models = []
        self.models_loaded = False
        self.device = self._get_device()
        logger.info(f"Using device: {self.device}")
    
    def initialize(self):
        """Load models on demand"""
        if not self.models_loaded:
            try:
                import demucs.pretrained
                from demucs.apply import apply_model
                from demucs.audio import AudioFile, save_audio
                
                # Make these methods available to other methods in the class
                self.apply_model = apply_model
                self.AudioFile = AudioFile
                self.save_audio = save_audio
                
                # Load demucs models
                self.models = demucs.pretrained.get_pretrained_models()
                self.models_loaded = True
                logger.info(f"Loaded {len(self.models)} demucs models")
            except ImportError as e:
                logger.error(f"Failed to load demucs models: {str(e)}")
                raise
    
    def _get_device(self) -> str:
        """Determine the best available device for processing"""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    
    def _get_model(self, model_name: str):
        """Get a specific demucs model"""
        self.initialize()
        
        if model_name == "all":
            return self.models.values()
            
        if model_name in self.models:
            return [self.models[model_name]]
        
        available_models = list(self.models.keys())
        logger.error(f"Model {model_name} not found. Available models: {available_models}")
        raise ValueError(f"Model {model_name} not found. Available models: {available_models}")
    
    def separate_track(self, 
                       input_file: str, 
                       output_dir: str, 
                       model_name: str = "htdemucs", 
                       stems: List[str] = None, 
                       progress_callback: Optional[Callable] = None) -> Dict:
        """
        Separate an audio track into stems
        
        Args:
            input_file: Path to input audio file
            output_dir: Directory to save separated tracks
            model_name: Name of demucs model to use
            stems: List of stems to extract (vocals, drums, bass, other)
            progress_callback: Callback function for progress updates
            
        Returns:
            Dictionary with separation results
        """
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Default stems if not specified
        if stems is None or len(stems) == 0:
            stems = ["vocals", "drums", "bass", "other"]
        
        # Create unique ID for this separation job
        job_id = str(uuid.uuid4())
        
        try:
            # Get model(s)
            models = self._get_model(model_name)
            
            # Import demucs components
            import torch
            from demucs.apply import apply_model
            from demucs.audio import AudioFile
            
            # Load audio file
            wav = AudioFile(input_file).read(streams=0, 
                                            samplerate=self.config['SAMPLE_RATE'], 
                                            channels=self.config['CHANNELS'])
            
            # Get filename without extension
            ref = os.path.basename(input_file).rsplit(".", 1)[0]
            
            # Track progress
            total_models = len(list(models))
            total_stems = len(stems)
            total_steps = total_models * total_stems
            current_step = 0
            
            result_files = []
            
            # Report initial progress
            if progress_callback:
                progress_callback(job_id, 0, "Loading audio file")
            
            # Process with each model
            for model in models:
                model_name = model.name
                
                # Report model progress
                if progress_callback:
                    progress_callback(job_id, int(current_step / total_steps * 100), 
                                    f"Processing with model: {model_name}")
                
                # Apply model
                sources = apply_model(model, wav.to(self.device), self.device)
                sources = sources.cpu()
                
                # Get source names from model
                source_names = model.sources
                
                # Process each requested stem
                for stem in stems:
                    if stem in source_names:
                        stem_idx = source_names.index(stem)
                        
                        # Create output filename
                        filename = f"{ref}_{model_name}_{stem}.wav"
                        output_path = os.path.join(output_dir, filename)
                        
                        # Save stem audio
                        self.save_audio(sources[..., stem_idx], 
                                        output_path, 
                                        sample_rate=self.config['SAMPLE_RATE'])
                        
                        result_files.append({
                            "path": output_path,
                            "name": filename,
                            "stem": stem,
                            "model": model_name
                        })
                    
                    # Update progress after each stem
                    current_step += 1
                    if progress_callback:
                        progress_callback(job_id, int(current_step / total_steps * 100), 
                                        f"Separated {stem} using {model_name}")
            
            # Report completion
            if progress_callback:
                progress_callback(job_id, 100, "Separation completed")
            
            # Return results
            return {
                "job_id": job_id,
                "input_file": input_file,
                "output_dir": output_dir,
                "model": model_name,
                "stems": stems,
                "files": result_files
            }
            
        except Exception as e:
            logger.error(f"Error during audio separation: {str(e)}")
            # Report error through callback
            if progress_callback:
                progress_callback(job_id, 0, f"Error: {str(e)}", "error")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available demucs models"""
        self.initialize()
        return list(self.models.keys()) 