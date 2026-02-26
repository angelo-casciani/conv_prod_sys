import argparse
import os
import sys
import logging
import shutil
import subprocess
import configparser
from pathlib import Path
from datetime import datetime, timedelta
from pm4py.objects.log.importer.xes import importer as xes_importer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutomatonLearner:
    def __init__(self, lsha_path=None):
        """
        Initialize the Automaton Learner with LSHA integration.
        
        Args:
            lsha_path: Path to the LSHA repository. If None, assumes it's in src/lsha.
        """
        if lsha_path is None:
            # LSHA is cloned in src/lsha
            self.lsha_path = Path(__file__).parent / "lsha"
        else:
            self.lsha_path = Path(lsha_path)
        
        if not self.lsha_path.exists():
            logger.error(f"LSHA repository not found at {self.lsha_path}")
            logger.error("Please clone it from: https://github.com/LesLivia/lsha/tree/xes_extension")
            logger.error(f"Expected location: {self.lsha_path}")
            raise FileNotFoundError(f"LSHA not found at {self.lsha_path}")
        
        logger.info(f"LSHA path configured: {self.lsha_path}")
    
    def configure_lsha_for_xes(self, xes_path, window_minutes=5):
        """
        Configure LSHA to process the given XES file with specified time window.
        
        Args:
            xes_path: Path to the XES event log
            window_minutes: Time window in minutes for learning
            
        Returns:
            tuple: (bool, start_time, end_time) - success status and time range
        """
        try:
            try:
                log = xes_importer.apply(str(xes_path))
                timestamps = [event['time:timestamp'] for trace in log for event in trace]
                first_event = min(timestamps)
                last_event = max(timestamps)
                logger.info(f"XES log time range: {first_event} to {last_event}")
                logger.info(f"Total traces: {len(log)}, Total events: {sum(len(t) for t in log)}")
                
                start_time = first_event
                end_time = start_time + timedelta(minutes=window_minutes)
                logger.info(f"Using time window: {start_time} to {end_time} ({window_minutes} minutes)")
                
            except Exception as e:
                logger.warning(f"Could not read XES timestamps: {e}")
                start_time = datetime(2025, 9, 5, 12, 30, 0) # Fallback to default times
                end_time = start_time + timedelta(minutes=window_minutes)
            
            config_path = self.lsha_path / "sha_learning" / "resources" / "config" / "config.ini"
            
            if not config_path.exists():
                logger.error(f"LSHA config file not found: {config_path}")
                return False, None, None
            
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Update configuration for XES processing
            if 'SUL CONFIGURATION' not in config:
                config['SUL CONFIGURATION'] = {}    
            config['SUL CONFIGURATION']['resample_strategy'] = 'XES'
            config['SUL CONFIGURATION']['case_study'] = 'LEGO_FACTORY'
            config['SUL CONFIGURATION']['cs_version'] = '1'
        
            if 'AUTO-TWIN CONFIGURATION' not in config: # Set time window based on actual log
                config['AUTO-TWIN CONFIGURATION'] = {}
            config['AUTO-TWIN CONFIGURATION']['pov'] = 'item'
            config['AUTO-TWIN CONFIGURATION']['start_date'] = start_time.strftime('%Y-%m-%d-%H-%M-%S')
            config['AUTO-TWIN CONFIGURATION']['end_date'] = end_time.strftime('%Y-%m-%d-%H-%M-%S')
            
            with open(config_path, 'w') as configfile:
                config.write(configfile)
            logger.info(f"LSHA configured for XES processing with {window_minutes} minute window")
            
            return True, start_time, end_time
            
        except Exception as e:
            logger.error(f"Error configuring LSHA: {e}", exc_info=True)
            return False, None, None
    
    def extract_skg(self, xes_path, output_path, window_minutes=5):
        """
        Extract SKG from XES event log using LSHA.
        Uses LSHA's built-in learn_and_convert_to_upp.py script via conda environment.
        
        Args:
            xes_path: Path to the input XES file
            output_path: Path where the UPPAAL XML file should be saved
            window_minutes: Time window in minutes for the learning algorithm (default: 5)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("Starting SKG extraction with LSHA")
            logger.info(f"Input XES: {xes_path}")
            logger.info(f"Output UPPAAL XML: {output_path}")
            logger.info(f"Time window: {window_minutes} minutes")
            logger.info("=" * 60)
            
            # Configure LSHA for this XES file and get time range
            success, start_time, end_time = self.configure_lsha_for_xes(xes_path, window_minutes)
            if not success:
                return False
            
            # Copy XES file to LSHA resources directory for processing
            lsha_xes_path = self.lsha_path / "resources" / "processed.xes"
            os.makedirs(lsha_xes_path.parent, exist_ok=True)
            shutil.copy(xes_path, lsha_xes_path)
            logger.info(f"XES file copied to LSHA resources: {lsha_xes_path}")
            
            # Find conda executable
            conda_paths = [
                Path.home() / "miniconda3" / "bin" / "conda",
                Path.home() / "anaconda3" / "bin" / "conda",
                Path("/opt/conda/bin/conda"),
            ]
            
            conda_exe = None
            for path in conda_paths:
                if path.exists():
                    conda_exe = str(path)
                    break
            
            if not conda_exe:
                # Try to find conda in PATH
                result = subprocess.run(["which", "conda"], capture_output=True, text=True)
                if result.returncode == 0:
                    conda_exe = result.stdout.strip()
            
            if not conda_exe:
                logger.error("Could not find conda installation. Please ensure conda is installed.")
                return False
            
            logger.info(f"Using conda: {conda_exe}")
            
            # Run LSHA using conda environment
            original_dir = os.getcwd()
            try:
                os.chdir(self.lsha_path)
                logger.info("Changed to LSHA directory for execution")
                
                logger.info("Learning in progress... This may take several minutes.")
                logger.info("Running LSHA's learn_and_convert_to_upp.py script via conda...")
                logger.info("-" * 60)
                
                # Run LSHA's built-in learning script with conda
                result = subprocess.run(
                    [conda_exe, "run", "-n", "lsha", "python", "learn_and_convert_to_upp.py"],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                # Log output
                if result.stdout:
                    for line in result.stdout.splitlines():
                        if "parsing log" in line or "%" in line or "it/s" in line:
                            continue  # Skip progress bars
                        logger.info(f"LSHA: {line}")
                
                if result.stderr:
                    for line in result.stderr.splitlines():
                        if line.strip() and "conda.cli" not in line:  # Skip conda warnings
                            logger.warning(f"LSHA: {line}")
                
                if result.returncode != 0:
                    logger.error(f"LSHA script failed with return code {result.returncode}")
                    return False
                
                logger.info("-" * 60)
                logger.info("LSHA learning completed!")
                
                # Find the generated UPPAAL file
                gen_models_dir = self.lsha_path / "uppaal_generator" / "resources" / "gen_models"
                if not gen_models_dir.exists():
                    logger.error(f"Generated models directory not found: {gen_models_dir}")
                    return False
                
                # Find the most recent XML file
                xml_files = list(gen_models_dir.glob("*.xml"))
                if not xml_files:
                    logger.error("No generated UPPAAL XML files found")
                    return False
                
                # Get the most recently modified file
                latest_file = max(xml_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"Found generated UPPAAL model: {latest_file.name}")
                
                # Copy to desired output location
                os.chdir(original_dir)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copy(latest_file, output_path)
                logger.info(f"UPPAAL model copied to: {output_path}")
                
                logger.info("SKG extraction completed successfully!")
                return True
                
            finally:
                # Always restore original directory
                os.chdir(original_dir)
                
        except subprocess.TimeoutExpired:
            logger.error("LSHA learning timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"Error during SKG extraction: {e}", exc_info=True)
            return False
    
    def copy_default_skg(self, output_path):
        """
        Copy the default SKG to the output location as fallback.
        
        Args:
            output_path: Path where the SKG should be copied
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            base_dir = Path(__file__).parent.parent
            default_skg_dir = base_dir / "data" / "automaton"
            
            # Find the default SKG file
            default_files = list(default_skg_dir.glob("*.xml"))
            if not default_files:
                logger.error(f"No default SKG found in {default_skg_dir}")
                return False
            
            default_skg = default_files[0]
            logger.info(f"Using default SKG: {default_skg.name}")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy(default_skg, output_path)
            
            logger.info(f"Default SKG copied to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying default SKG: {e}", exc_info=True)
            return False
    
    def learn_automaton(self, xes_path, output_name="learned_skg.xml", window_minutes=5):
        """
        Main method to learn automaton from XES log with fallback to default.
        
        Args:
            xes_path: Path to the input XES file
            output_name: Name for the output UPPAAL XML file
            window_minutes: Time window in minutes for the learning algorithm
            
        Returns:
            str: Path to the generated (or default) SKG file, or None if failed
        """
        base_dir = Path(__file__).parent.parent
        output_path = base_dir / "data" / "automaton" / output_name
        
        # Ensure output directory exists
        os.makedirs(output_path.parent, exist_ok=True)
        
        # Try to extract SKG
        success = self.extract_skg(xes_path, output_path, window_minutes)
        
        if not success:
            logger.warning("=" * 60)
            logger.warning("SKG extraction failed, falling back to default SKG")
            logger.warning("=" * 60)
            success = self.copy_default_skg(output_path)
            if not success:
                logger.error("Failed to use default SKG")
                return None
        
        return str(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Learn automaton from XES event log')
    parser.add_argument('xes_file', help='Path to XES event log file')
    parser.add_argument('--output', '-o', help='Output file name', default='learned_skg.xml')
    parser.add_argument('--window', '-w', type=int, help='Time window in minutes', default=5)
    
    args = parser.parse_args()
    
    try:
        learner = AutomatonLearner()
        result = learner.learn_automaton(args.xes_file, args.output, args.window)
        
        if result:
            print(f"\n{'='*60}")
            print(f"SUCCESS: SKG saved to: {result}")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print("FAILED: Could not generate SKG")
            print(f"{'='*60}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
