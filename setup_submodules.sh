#!/bin/bash
set -e 
echo "============================================="
echo "Setting up Git Submodules for conv_prod_sys"
echo "============================================="
echo ""

# Initialize and update all submodules
echo "Initializing and updating git submodules..."
git submodule update --init --recursive
echo "Submodules initialized and updated"
echo ""

echo "============================================="
echo "Setting up Fast Downward (PDDL Planner)"
echo "============================================="
echo ""

# Check if Fast Downward is properly initialized
if [ -f "src/pddl/downward/fast-downward.py" ]; then
    echo "Fast Downward found"
    
    # Check if Fast Downward is already built
    if [ -d "src/pddl/downward/builds" ]; then
        echo "Fast Downward appears to be already built"
        echo ""
    else
        echo "Building Fast Downward..."
        cd src/pddl/downward
        
        if [ -f "./build.py" ]; then
            ./build.py
            echo "Fast Downward built successfully"
        else
            echo "Error: build.py not found in src/pddl/downward"
            exit 1
        fi
        cd ../../..
        echo ""
    fi
else
    echo "Error: Fast Downward submodule not properly initialized"
    echo "Please check the .gitmodules file and ensure the repository is cloned correctly"
    exit 1
fi

echo "============================================="
echo "Setting up DTLogExtSim (Digital Twin Extractor)"
echo "============================================="
echo ""

# Check if DTLogExtSim is properly initialized
if [ -f "src/DTLogExtSim/docker-compose.yml" ]; then
    echo "DTLogExtSim found"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo "Warning: Docker not found. DTLogExtSim requires Docker to run."
        echo "Please install Docker from https://www.docker.com"
        echo ""
    else
        echo "Docker found"
        
        # Check if docker compose is available
        if docker compose version &> /dev/null; then
            echo "Docker Compose found"
            echo ""
            echo "DTLogExtSim is ready to use!"
            echo "To run DTLogExtSim:"
            echo "  cd src/DTLogExtSim"
            echo "  docker compose up --build"
            echo "Then access the UI at http://127.0.0.1:6660"
        else
            echo "Warning: Docker Compose not found or not working"
            echo "Please ensure Docker Compose is properly installed"
        fi
    fi
    echo ""
    
    # Create extractor_outputs directory if it doesn't exist
    if [ ! -d "src/extractor_outputs" ]; then
        echo "Creating extractor_outputs directory..."
        mkdir -p src/extractor_outputs
        echo "Created src/extractor_outputs"
    else
        echo "extractor_outputs directory already exists"
    fi
    echo ""
    
    # Check if the volume mount is configured in docker-compose.yml
    if grep -q "extractor_outputs:/app/extractor" "src/DTLogExtSim/docker-compose.yml"; then
        echo "Volume mount for extractor_outputs is already configured"
    else
        echo "Note: You may need to add the volume mount to src/DTLogExtSim/docker-compose.yml"
        echo "Add this line under the extractor service volumes section:"
        echo "  - ./../extractor_outputs:/app/extractor"
    fi
else
    echo "Error: DTLogExtSim submodule not properly initialized"
    echo "Please check the .gitmodules file and ensure the repository is cloned correctly"
    exit 1
fi

echo ""
echo "============================================="
echo "Setup Complete!"
echo "============================================="
echo ""
echo "Submodules initialized:"
echo "  ✓ Fast Downward (PDDL Planner) at src/pddl/downward"
echo "  ✓ DTLogExtSim (Digital Twin Extractor) at src/DTLogExtSim"
echo ""
echo "Next steps:"
echo "  1. Ensure UPPAAL is installed and activated (see README.md)"
echo "  2. Set up your .env file with API keys"
echo "  3. Run 'pip install -r requirements.txt' if not already done"
echo "  4. Run 'python src/main.py' to start the framework"
echo ""
