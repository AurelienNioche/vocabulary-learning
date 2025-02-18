#!/bin/bash

# Colors for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to print colored messages
print_step() {
    echo -e "${BLUE}==>${NC} ${BOLD}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    if [ "$2" = "exit" ]; then
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}" "exit"
    fi
}

# Get script directory (macOS compatible)
get_script_dir() {
    SOURCE=${BASH_SOURCE[0]}
    while [ -L "$SOURCE" ]; do
        DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
        SOURCE=$(readlink "$SOURCE")
        [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE
    done
    cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd
}

# Get appropriate data directory
get_data_dir() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "$HOME/Library/Application Support/VocabularyLearning"
    else
        echo "$HOME/.local/share/vocabulary-learning"
    fi
}

# Function to setup environment
setup_environment() {
    local data_dir="$1"
    local env_file="$data_dir/.env"
    
    if [ ! -f "$env_file" ]; then
        print_step "Creating .env file..."
        
        # Get Firebase configuration
        read -p "Enter your Firebase Database URL: " db_url
        read -p "Enter your Firebase User Email: " user_email
        read -p "Enter your timezone (default: Europe/Helsinki): " timezone
        timezone=${timezone:-"Europe/Helsinki"}
        
        cat > "$env_file" << EOL
FIREBASE_CREDENTIALS_PATH="${data_dir}/firebase/credentials.json"
FIREBASE_DATABASE_URL="${db_url}"
FIREBASE_USER_EMAIL="${user_email}"
TIMEZONE=${timezone}
EOL
        print_success ".env file created"
    else
        print_success ".env file already exists"
    fi
}

# Function to setup Firebase credentials
setup_firebase() {
    local data_dir="$1"
    local creds_dir="$data_dir/firebase"
    local creds_file="$creds_dir/credentials.json"
    
    if [ ! -f "$creds_file" ]; then
        print_step "Firebase credentials setup"
        mkdir -p "$creds_dir"
        echo "Please copy your Firebase credentials JSON file to:"
        echo "$creds_file"
        echo "You can get this file from your Firebase Console > Project Settings > Service Accounts"
        read -p "Press Enter once you've copied the credentials file..."
        
        if [ ! -f "$creds_file" ]; then
            print_error "credentials.json not found in firebase directory" "exit"
        fi
    fi
}

# Main installation process
main() {
    print_step "Checking dependencies..."
    check_dependencies
    print_success "All dependencies found"
    
    # Create necessary directories
    DATA_DIR="$(get_data_dir)"
    mkdir -p "$DATA_DIR/data"
    mkdir -p "$DATA_DIR/firebase"
    print_success "Directories created at $DATA_DIR"
    
    # Setup environment and Firebase
    setup_environment "$DATA_DIR"
    setup_firebase "$DATA_DIR"
    
    # Build Docker image
    print_step "Building Docker image..."
    if ! docker build -t vocab-learning .; then
        print_error "Failed to build Docker image" "exit"
    fi
    print_success "Docker image built successfully"
    
    # Create the vocab command
    print_step "Creating vocab command..."
    INSTALL_DIR="$(pwd)"
    
    cat > vocab-docker << EOL
#!/bin/bash
docker run -it --rm \\
  -v "$(get_data_dir)":/app/data \\
  vocab-learning
EOL
    chmod +x vocab-docker
    
    # Determine the appropriate bin directory and create symlink
    if [[ "$OSTYPE" == "darwin"* ]]; then
        BIN_DIR="$HOME/bin"
        mkdir -p "$BIN_DIR"
        
        # Add to PATH if needed
        if ! grep -q "export PATH=\"\$HOME/bin:\$PATH\"" "$HOME/.zshrc" 2>/dev/null; then
            echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
            print_step "Added ~/bin to PATH in .zshrc"
            print_step "Please run: source ~/.zshrc"
        fi
        
        ln -sf "$INSTALL_DIR/vocab-docker" "$BIN_DIR/vocab"
        print_success "Created 'vocab' command in ~/bin"
    else
        if sudo -n true 2>/dev/null; then
            sudo ln -sf "$INSTALL_DIR/vocab-docker" "/usr/local/bin/vocab"
            print_success "Created 'vocab' command in /usr/local/bin"
        else
            print_error "Could not create system-wide command. You can still use: ./vocab-docker"
        fi
    fi
    
    # Final success message
    echo
    echo -e "${GREEN}${BOLD}Installation completed successfully!${NC}"
    echo
    echo "Your data will be stored in:"
    echo "- $DATA_DIR/data/ (vocabulary and progress)"
    echo "- $DATA_DIR/firebase/ (credentials)"
    echo "- $DATA_DIR/.env (configuration)"
    echo
    echo "To start the vocabulary learning tool, simply run:"
    echo -e "${BOLD}vocab${NC}"
}

# Run main installation
main 