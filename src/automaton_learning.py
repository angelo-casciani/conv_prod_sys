import os
import sys
import logging
import shutil
import configparser
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
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
        
        # Add LSHA to Python path
        if str(self.lsha_path) not in sys.path:
            sys.path.insert(0, str(self.lsha_path))
        
        logger.info(f"LSHA path configured: {self.lsha_path}")
    
    def configure_lsha_for_xes(self, xes_path, window_minutes=5):
        """
        Configure LSHA to process the given XES file with specified time window.
        
        Args:
            xes_path: Path to the XES event log
            window_minutes: Time window in minutes for learning
            
        Returns:
            bool: True if configuration successful
        """
        try:
            config_path = self.lsha_path / "sha_learning" / "resources" / "config" / "config.ini"
            
            if not config_path.exists():
                logger.error(f"LSHA config file not found: {config_path}")
                return False
            
            # Read current config
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Update configuration for XES processing
            if 'SUL CONFIGURATION' not in config:
                config['SUL CONFIGURATION'] = {}
            
            config['SUL CONFIGURATION']['RESAMPLE_STRATEGY'] = 'XES'
            config['SUL CONFIGURATION']['CASE_STUDY'] = 'LEGO_FACTORY'
            
            # Set time window (using example dates - LSHA will process based on actual log timestamps)
            if 'AUTO-TWIN CONFIGURATION' not in config:
                config['AUTO-TWIN CONFIGURATION'] = {}
            
            # Use a time window of specified minutes
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=window_minutes)
            
            config['AUTO-TWIN CONFIGURATION']['START_DATE'] = start_time.strftime('%Y-%m-%d-%H-%M-%S')
            config['AUTO-TWIN CONFIGURATION']['END_DATE'] = end_time.strftime('%Y-%m-%d-%H-%M-%S')
            
            # Write updated config
            with open(config_path, 'w') as configfile:
                config.write(configfile)
            
            logger.info(f"LSHA configured for XES processing with {window_minutes} minute window")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring LSHA: {e}", exc_info=True)
            return False
    
    def extract_skg(self, xes_path, output_path, window_minutes=5):
        """
        Extract SKG (Stochastic Knowledge Graph) from XES event log using LSHA.
        
        Args:
            xes_path: Path to the input XES file
            output_path: Path where the UPPAAL XML file should be saved
            window_minutes: Time window in minutes for the learning algorithm
            
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
            
            # Configure LSHA for this XES file
            if not self.configure_lsha_for_xes(xes_path, window_minutes):
                return False
            
            # Copy XES file to LSHA resources directory for processing
            lsha_xes_path = self.lsha_path / "resources" / "processed.xes"
            os.makedirs(lsha_xes_path.parent, exist_ok=True)
            shutil.copy(xes_path, lsha_xes_path)
            logger.info(f"XES file copied to LSHA resources: {lsha_xes_path}")
            
            # Import and run LSHA (need to be in LSHA directory for relative paths)
            original_dir = os.getcwd()
            try:
                os.chdir(self.lsha_path)
                logger.info("Changed to LSHA directory for execution")
                
                # Set Neo4j environment variables (required by LSHA even if not used)
                os.environ['NEO4J_URI'] = 'empty'
                os.environ['NEO4J_USERNAME'] = 'empty'
                os.environ['NEO4J_PASSWORD'] = 'empty'
                os.environ['NEO4J_SCHEMA'] = 'empty'
                
                logger.info("Learning in progress... This may take several minutes.")
                logger.info("Progress will be logged below:")
                logger.info("-" * 60)
                
                # Import LSHA modules
                import warnings
                warnings.filterwarnings('ignore')
                
                from sha_learning.case_studies.lego_factory.sul_definition import getSUL
                from sha_learning.domain.lshafeatures import Trace
                from sha_learning.domain.obstable import ObsTable
                from sha_learning.learning_setup.learner import Learner
                from sha_learning.learning_setup.teacher import Teacher
                import sha_learning.pltr.sha_pltr as ha_pltr
                from uppaal_generator.model_generator.sha2uppaal import generate_upp_model
                from uppaal_generator.model_generator.dot2sha import parse_sha
                
                logger.info("LSHA modules imported successfully")
                
                # Get System Under Learning
                SUL, events_labels_dict = getSUL()
                logger.info("System Under Learning (SUL) initialized")
                
                # Create teacher and learner
                TEACHER = Teacher(SUL)
                long_traces = [Trace(events=[e]) for e in SUL.events]
                obs_table = ObsTable([], [Trace(events=[])], long_traces)
                LEARNER = Learner(TEACHER, obs_table)
                logger.info("Teacher and Learner initialized")
                
                # Run learning algorithm
                logger.info("Running LSHA learning algorithm...")
                LEARNED_HA = LEARNER.run_lsha(filter_empty=True)
                logger.info("Learning completed!")
                
                # Save learned SHA
                sha_save_path = "sha_learning/resources/learned_sha/"
                os.makedirs(sha_save_path, exist_ok=True)
                
                cs_name = f"learned_skg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                graphviz_sha = ha_pltr.to_graphviz(LEARNED_HA, cs_name, sha_save_path, view=False)
                
                # Save SHA source
                sha_source = graphviz_sha.source
                sha_source_path = os.path.join(sha_save_path, f"{cs_name}_source.txt")
                with open(sha_source_path, 'w') as f:
                    f.write(sha_source)
                logger.info(f"SHA source saved to: {sha_source_path}")
                
                # Convert to UPPAAL format
                logger.info("Converting SHA to UPPAAL format...")
                automaton_path = os.path.join(sha_save_path, cs_name)
                sha = parse_sha(automaton_path, cs_name)
                
                # Use default acquisition bounds (can be customized if needed)
                from sha_learning.case_studies.lego_factory.sul_functions import get_acquisition_bounds
                automaton_start, automaton_end = get_acquisition_bounds()
                
                model_path = generate_upp_model(sha, cs_name, automaton_start, automaton_end)
                logger.info(f"UPPAAL model generated: {model_path}")
                
                # Copy generated UPPAAL file to desired output location
                os.chdir(original_dir)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copy(model_path, output_path)
                logger.info(f"UPPAAL model copied to: {output_path}")
                
                logger.info("-" * 60)
                logger.info("SKG extraction completed successfully!")
                return True
                
            finally:
                # Always restore original directory
                os.chdir(original_dir)
                
        except ImportError as e:
            logger.error(f"Failed to import LSHA modules: {e}", exc_info=True)
            logger.error("Make sure LSHA dependencies are installed: pip install -r src/lsha/requirements.txt")
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
            default_skg_dir = base_dir / "data" / "automaton" / "default"
            
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
    # Example usage
    import argparse
    
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
