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
echo "Setting up LSHA Automaton Learner"
echo "============================================="
echo ""

if [ -d "src/lsha" ]; then
    echo "LSHA submodule found"
    
    # Check if it's a proper submodule
    if git config --file .gitmodules --get-regexp 'submodule.src/lsha' > /dev/null 2>&1; then
        echo "LSHA is properly configured as a submodule"
        
        # Set up LSHA conda environment
        if command -v conda &> /dev/null; then
            echo "Conda found. Setting up LSHA conda environment..."
            
            # Check if environment is already created
            if conda env list | grep -q "^lsha "; then
                echo "LSHA conda environment already exists"
                echo "To update it, run: conda env update -f src/lsha/environment.yml --prune"
            else
                echo "Creating LSHA conda environment from src/lsha/environment.yml..."
                conda env create -f src/lsha/environment.yml
                echo "LSHA conda environment created successfully"
                echo ""
                echo "To activate it later, run: conda activate lsha"
            fi
        else
            echo "WARNING: conda not found in PATH"
            echo "LSHA requires a separate conda environment due to dependency conflicts"
            echo "Please install conda and run the following to set up LSHA:"
            echo "   conda env create -f src/lsha/environment.yml"
            echo "Install conda from: https://docs.conda.io/en/latest/miniconda.html"
        fi
        
        # Verify LSHA dependencies are documented
        if [ -f "src/lsha/requirements.txt" ]; then
            echo "LSHA has additional dependencies (see src/lsha/requirements.txt)"
        fi
    else
        echo "WARNING: LSHA directory exists but is not a submodule"
        echo "Attempting to convert to submodule..."
        
        # Backup existing directory
        if [ -d "src/lsha.backup" ]; then
            rm -rf src/lsha.backup
        fi
        cp -r src/lsha src/lsha.backup
        echo "Backup created at src/lsha.backup"
        
        # Remove and re-add as submodule
        rm -rf src/lsha
        git submodule add -b xes_extension https://github.com/LesLivia/lsha.git src/lsha
        git submodule update --init --recursive src/lsha
        
        if [ -f "src/lsha/README.md" ]; then
            echo "LSHA successfully converted to submodule"
            echo "You can remove backup with: rm -rf src/lsha.backup"
        else
            echo "ERROR: Failed to convert LSHA to submodule"
            exit 1
        fi
    fi
else
    echo "LSHA submodule not found"
    echo "Adding LSHA as submodule..."
    git submodule add -b xes_extension https://github.com/LesLivia/lsha.git src/lsha
    git submodule update --init --recursive src/lsha
    
    if [ -f "src/lsha/README.md" ]; then
        echo "LSHA submodule added successfully"
        
        # Set up LSHA conda environment
        if command -v conda &> /dev/null; then
            echo "Setting up LSHA conda environment..."
            if conda env list | grep -q "^lsha "; then
                echo "LSHA conda environment already exists"
            else
                echo "Creating LSHA conda environment from src/lsha/environment.yml..."
                conda env create -f src/lsha/environment.yml
                echo "LSHA conda environment created successfully"
            fi
        else
            echo "WARNING: conda not found - LSHA requires conda for dependency isolation"
            echo "Please install conda and run: conda env create -f src/lsha/environment.yml"
        fi
    else
        echo "ERROR: Failed to add LSHA submodule"
        exit 1
    fi
fi
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
if [ -d "src/lsha" ] && [ -f "src/lsha/README.md" ]; then
    echo "  ✓ LSHA (Automaton Learning) at src/lsha"
    if conda env list | grep -q "^lsha "; then
        echo "    └─ Conda environment 'lsha' successfully created"
    else
        echo "    └─ WARNING: Conda environment 'lsha' not found"
    fi
else
    echo "  ⚠ LSHA initialization failed"
fi
echo ""
echo "Python Environments:"
echo "  ✓ Main venv (.venv) - for framework components"
echo "  ✓ LSHA conda (lsha) - for automaton learning (isolated dependencies)"
echo ""
echo "Components:"
echo "  ✓ DTLogExtSim Extractor at src/DTLogExtSim/Extractor"
echo "  ✓ SKG Automaton Learning with LSHA (data/automaton/)"
echo "  ✓ UPPAAL (Verification Engine) with Docker support"
echo ""
echo "Next steps:"
echo "  1. Activate main venv:       source .venv/bin/activate"
echo "  2. Install dependencies:     pip install -r requirements.txt"
echo "  3. Set up .env with API keys and UPPAAL_LICENSE_KEY (if not done)"
echo "  4. Start framework:          python src/main.py (CLI) or python src/chatbot.py (GUI)"
echo ""
echo "For LSHA automaton learning:"
echo "  - Activate LSHA environment: conda activate lsha"
echo "  - It is automatically invoked by automaton_learning.py via subprocess"
echo ""