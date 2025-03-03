#!/bin/bash

# Colors for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Default timezone (should match DEFAULT_TIMEZONE in constants.py)
DEFAULT_TIMEZONE="Europe/Helsinki"

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
        read -p "Enter your timezone (default: ${DEFAULT_TIMEZONE}): " timezone
        timezone=${timezone:-"${DEFAULT_TIMEZONE}"}
        
        cat > "$env_file" << EOL
FIREBASE_CREDENTIALS_PATH="${data_dir}/firebase/credentials.json"
FIREBASE_DATABASE_URL="${db_url}"
FIREBASE_USER_EMAIL="${user_email}"
TIMEZONE=${timezone}
EOL
        
        print_success "Created .env file"
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

# Main installation
main() {
    print_step "Starting installation..."
    
    # Check dependencies
    check_dependencies
    
    # Get data directory
    data_dir=$(get_data_dir)
    
    # Create necessary directories
    print_step "Creating directories..."
    mkdir -p "${data_dir}/data"
    mkdir -p "${data_dir}/firebase"
    print_success "Created directories"
    
    # Setup environment
    setup_environment "$data_dir"
    setup_firebase "$data_dir"
    
    # Build Docker image
    print_step "Building Docker image..."
    docker build -t vocab-learning .
    print_success "Built Docker image"
    
    # Create vocab command
    print_step "Creating vocab command..."
    sudo ln -sf "$(pwd)/vocab" /usr/local/bin/vocab
    print_success "Created vocab command"
    
    print_success "Installation complete!"
    echo -e "\nYou can now run the program with the 'vocab' command"
}

main 