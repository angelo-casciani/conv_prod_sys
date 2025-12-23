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
echo "Setting up UPPAAL with Docker"
echo "============================================="
echo ""

# Check if UPPAAL directory exists
if [ -d "src/uppaal" ]; then
    echo "UPPAAL installation found in src/uppaal"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            echo "Creating .env file from template..."
            cp .env.example .env
            echo "⚠️  Please edit .env file and add your UPPAAL_LICENSE_KEY"
            echo "   Get your license from: https://uppaal.veriaal.dk"
        fi
    fi
    
    # Check if license key is set
    if [ -f ".env" ] && grep -q "UPPAAL_LICENSE_KEY" ".env"; then
        source .env
        if [ -z "$UPPAAL_LICENSE_KEY" ] || [ "$UPPAAL_LICENSE_KEY" = "your_license_key_here" ]; then
            echo "⚠️  Please set UPPAAL_LICENSE_KEY in .env file"
            echo "   Get your license from: https://uppaal.veriaal.dk"
        else
            echo "UPPAAL license key found in .env"
            
            # Check if Docker is available
            if command -v docker &> /dev/null; then
                echo "Building UPPAAL Docker image..."
                if sudo docker build --build-arg KEY=$UPPAAL_LICENSE_KEY -t uppaal-engine:latest -f Dockerfile.uppaal ./src/uppaal 2>&1 | grep -q "Successfully"; then
                    echo "✓ UPPAAL Docker image built successfully"
                    
                    # Start the container
                    echo "Starting UPPAAL container..."
                    if sudo docker ps | grep -q uppaal-engine; then
                        echo "UPPAAL container already running"
                    else
                        sudo docker run --rm -d --name uppaal-engine -p 2350:2350 \
                            -v "$PWD/data/automaton:/home/uppaal/models:ro" \
                            -e UPPAAL_LICENSE_KEY=$UPPAAL_LICENSE_KEY \
                            uppaal-engine:latest
                        sleep 2
                        
                        if sudo docker ps | grep -q uppaal-engine; then
                            echo "✓ UPPAAL container is running"
                        else
                            echo "⚠️  Failed to start UPPAAL container"
                        fi
                    fi
                else
                    echo "⚠️  Failed to build UPPAAL Docker image"
                fi
            else
                echo "⚠️  Docker not found. UPPAAL Docker setup requires Docker."
                echo "   You can install UPPAAL manually or install Docker to use containerized UPPAAL"
            fi
        fi
    fi
else
    echo "⚠️  UPPAAL installation not found in src/uppaal"
    echo "   Please download UPPAAL for Linux from https://uppaal.org/downloads/"
    echo "   and extract it to src/uppaal/"
fi

echo ""
echo "============================================="
echo "Setup Complete!"
echo "============================================="
echo ""
echo "Submodules initialized:"
echo "  ✓ Fast Downward (PDDL Planner) at src/pddl/downward"
echo "  ✓ DTLogExtSim (Digital Twin Extractor) at src/DTLogExtSim"
echo "  ✓ UPPAAL (Verification Engine) with Docker support"
echo ""
echo "Next steps:"
echo "  1. Set up your .env file with API keys and UPPAAL_LICENSE_KEY (if not done)"
echo "  2. Run 'pip install -r requirements.txt' if not already done"
echo "  3. Run 'python src/main.py' to start the framework"
echo ""
echo "UPPAAL Docker commands:"
echo "  Stop:  sudo docker stop uppaal-engine"
echo "  Start: sudo docker run --rm -d --name uppaal-engine -p 2350:2350 \\"
echo "           -v \$PWD/data/automaton:/home/uppaal/models:ro \\"
echo "           -e UPPAAL_LICENSE_KEY=\$UPPAAL_LICENSE_KEY uppaal-engine:latest"
echo "  Test:  python src/uppaal_interface.py"
echo ""
