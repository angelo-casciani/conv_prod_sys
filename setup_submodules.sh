#!/bin/bash
set -e 
echo "============================================="
echo "Setting up Git Submodules for conv_prod_sys"
echo "============================================="
echo ""

echo "Initializing and updating git submodules..."
git submodule update --init --recursive
echo "Submodules initialized and updated"
echo ""

echo "============================================="
echo "Setting up Fast Downward Planner"
echo "============================================="
echo ""

if [ -f "src/downward/fast-downward.py" ]; then
    echo "Fast Downward found"
    
    if [ -d "src/downward/builds" ]; then
        echo "Fast Downward appears to be already built"
        echo ""
    else
        echo "Building Fast Downward..."
        cd src/downward
        
        if [ -f "./build.py" ]; then
            ./build.py release
            echo "Fast Downward built successfully"
        else
            echo "Error: build.py not found in src/downward"
            exit 1
        fi
        cd ../..
        echo ""
    fi
else
    echo "Error: Fast Downward submodule not properly initialized"
    echo "Please check the .gitmodules file and ensure the repository is cloned correctly"
    exit 1
fi

if [ ! -d "src/extractor_outputs" ]; then
    echo "Creating extractor_outputs directory..."
    mkdir -p src/extractor_outputs
    echo "Created src/extractor_outputs"
else
    echo "extractor_outputs directory already exists"
fi
echo ""


echo "============================================="
echo "Setting up Docker Services"
echo "============================================="
echo ""

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env file from template..."
        cp .env.example .env
        echo "Please edit .env file and add your UPPAAL_LICENSE_KEY"
        echo "   Get your license from: https://uppaal.veriaal.dk"
    else
        echo "No .env file found. Please create one with UPPAAL_LICENSE_KEY"
        echo "   Get your license from: https://uppaal.veriaal.dk"
    fi
fi

# Check if license key is set
if [ -f ".env" ] && grep -q "UPPAAL_LICENSE_KEY" ".env"; then
    source .env
    if [ -z "$UPPAAL_LICENSE_KEY" ] || [ "$UPPAAL_LICENSE_KEY" = "your_license_key_here" ]; then
        echo "Please set UPPAAL_LICENSE_KEY in .env file"
        echo "   Get your license from: https://uppaal.veriaal.dk"
    else
        echo "UPPAAL license key found in .env"
        
        if command -v docker &> /dev/null; then
            echo "Docker found"
            
            if docker images | grep -q uppaal-engine; then
                echo "UPPAAL Docker image already exists"
            else
                echo "UPPAAL Docker image not found"
                echo "   You need to build it first from the UPPAAL installation"
                echo "   See README for instructions"
            fi
            
            # Start/restart using docker-compose
            if [ -f "docker-compose.yml" ]; then
                echo "Starting containers using docker-compose..."
                sudo docker compose up -d
                
                sleep 2
                if sudo docker ps | grep -q uppaal-engine; then
                    echo "UPPAAL container is running on port 2350"
                else
                    echo "UPPAAL container failed to start. Check logs with:"
                    echo "   sudo docker logs uppaal-engine"
                fi
                
                if sudo docker ps | grep -q extractor; then
                    echo "Extractor container is running on port 6662"
                else
                    echo "Extractor container failed to start. Check logs with:"
                    echo "   sudo docker logs <extractor-container-name>"
                fi
            else
                echo "docker-compose.yml not found"
            fi
        else
            echo "Docker not found. UPPAAL Docker setup requires Docker."
            echo "   Install Docker from https://www.docker.com"
        fi
    fi
else
    echo "No UPPAAL_LICENSE_KEY found in .env file"
fi

echo ""
echo "============================================="
echo "Setup Complete!"
echo "============================================="
echo ""
echo "Submodules initialized:"
echo "  ✓ Fast Downward (PDDL Planner) at src/downward"
echo ""
echo "Components:"
echo "  ✓ DTLogExtSim Extractor at src/DTLogExtSim/Extractor"
echo "  ✓ UPPAAL (Verification Engine) with Docker support"
echo ""
echo "Next steps:"
echo "  1. Set up your .env file with API keys and UPPAAL_LICENSE_KEY (if not done)"
echo "  2. Run 'pip install -r requirements.txt' if not already done"
echo "  3. Run 'python src/main.py' to start the framework on CLI or 'python src/chatbot.py' to start the GUI."
echo ""