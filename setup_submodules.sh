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

# Determine if we need sudo for docker
DOCKER_CMD="docker"
DOCKER_COMPOSE_CMD="docker-compose"
if ! docker info &> /dev/null; then
    if sudo docker info &> /dev/null; then
        echo "Docker requires sudo on this system"
        DOCKER_CMD="sudo docker"
        DOCKER_COMPOSE_CMD="sudo docker-compose"
    fi
fi

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
            
            # Download and setup UPPAAL if not present
            if [ ! -d "src/uppaal" ]; then
                echo "Downloading UPPAAL 5.0.0..."
                wget -q --show-progress https://download.uppaal.org/uppaal-5.0/uppaal-5.0.0/uppaal-5.0.0-linux64.zip -O /tmp/uppaal.zip
                echo "Extracting UPPAAL..."
                unzip -q /tmp/uppaal.zip -d /tmp/
                mv /tmp/uppaal-5.0.0-linux64 src/uppaal
                rm /tmp/uppaal.zip
                echo "UPPAAL installed to src/uppaal"
                
                # Create the Dockerfile for UPPAAL
                mkdir -p src/uppaal/res
                cat > src/uppaal/res/Dockerfile << 'EOF'
FROM ubuntu:22.04

RUN useradd -ms /bin/bash uppaal
RUN apt-get -qq update && apt-get -qq upgrade -y
USER uppaal
ENV USER=uppaal
WORKDIR /home/uppaal
ADD . uppaal
ENV PATH="/home/uppaal/uppaal/bin:$PATH"
ARG KEY=""
ARG LEASE="1"
RUN verifyta.sh --key ${KEY} --lease ${LEASE}
RUN verifyta.sh --version

EXPOSE 2350
CMD /home/uppaal/uppaal/bin/socketserver.sh /home/uppaal/uppaal/bin/server.sh
EOF
                echo "Created UPPAAL Dockerfile"
            else
                echo "UPPAAL already installed at src/uppaal"
            fi
            
            # Build UPPAAL Docker image if not exists
            if $DOCKER_CMD images | grep -q uppaal-engine; then
                echo "UPPAAL Docker image already exists"
            else
                echo "Building UPPAAL Docker image..."
                cd src/uppaal
                $DOCKER_CMD build --build-arg KEY=$UPPAAL_LICENSE_KEY --tag uppaal-engine -f res/Dockerfile .
                cd ../..
                echo "UPPAAL Docker image built successfully"
            fi
            
            # Start/restart using docker-compose
            if [ -f "docker-compose.yml" ]; then
                echo "Starting containers using docker-compose..."
                $DOCKER_COMPOSE_CMD up -d
                
                sleep 2
                if $DOCKER_CMD ps | grep -q uppaal-engine; then
                    echo "UPPAAL container is running on port 2350"
                else
                    echo "UPPAAL container failed to start. Check logs with:"
                    echo "   $DOCKER_CMD logs uppaal-engine"
                fi
                
                if $DOCKER_CMD ps | grep -q extractor; then
                    echo "Extractor container is running on port 6662"
                else
                    echo "Extractor container failed to start. Check logs with:"
                    echo "   $DOCKER_CMD logs extractor-service"
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