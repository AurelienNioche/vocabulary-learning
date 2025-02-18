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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Create necessary directories
print_step "Creating necessary directories..."
DATA_DIR="$(get_data_dir)"
mkdir -p "$DATA_DIR/data"
mkdir -p "$DATA_DIR/firebase"
print_success "Directories created at $DATA_DIR"

# Copy default vocabulary if needed
if [ ! -f "$DATA_DIR/data/vocabulary.json" ]; then
    print_step "Copying default vocabulary..."
    cp vocabulary_learning/package_data/vocabulary.json "$DATA_DIR/data/"
    print_success "Default vocabulary copied"
fi

# Check if .env file exists
if [ ! -f "$DATA_DIR/.env" ]; then
    print_step "Creating .env file..."
    echo "We need some information for Firebase configuration."
    echo
    read -p "Enter your Firebase Database URL: " db_url
    read -p "Enter your Firebase User Email: " user_email
    
    cat > "$DATA_DIR/.env" << EOL
FIREBASE_CREDENTIALS_PATH=/app/firebase/credentials.json
FIREBASE_DATABASE_URL=${db_url}
FIREBASE_USER_EMAIL=${user_email}
EOL
    print_success ".env file created"
else
    print_success ".env file already exists"
fi

# Check for Firebase credentials
if [ ! -f "$DATA_DIR/firebase/credentials.json" ]; then
    print_step "Firebase credentials setup"
    echo "Please copy your Firebase credentials JSON file to:"
    echo "$DATA_DIR/firebase/credentials.json"
    echo "You can get this file from your Firebase Console > Project Settings > Service Accounts"
    read -p "Press Enter once you've copied the credentials file..."
    
    if [ ! -f "$DATA_DIR/firebase/credentials.json" ]; then
        print_error "credentials.json not found in firebase directory"
        exit 1
    fi
fi

# Build Docker image
print_step "Building Docker image..."
if docker build -t vocab-learning .; then
    print_success "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Create the vocab command
print_step "Creating vocab command..."
cat > vocab-docker << EOL
#!/bin/bash
docker run -it --rm \\
  -v "$(get_data_dir)/data":/app/vocabulary_learning/data \\
  -v "$(get_data_dir)/firebase":/app/firebase \\
  -v "$(get_data_dir)/.env":/app/.env \\
  vocab-learning
EOL
chmod +x vocab-docker

# Determine the appropriate bin directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - prefer ~/bin if it exists in PATH, otherwise create it
    if [[ ":$PATH:" == *":$HOME/bin:"* ]]; then
        BIN_DIR="$HOME/bin"
    else
        BIN_DIR="$HOME/bin"
        mkdir -p "$BIN_DIR"
        # Add to PATH if not already in shell config
        if ! grep -q "export PATH=\"\$HOME/bin:\$PATH\"" "$HOME/.zshrc" 2>/dev/null; then
            echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
            print_step "Added ~/bin to PATH in .zshrc"
            print_step "Please run: source ~/.zshrc"
        fi
    fi
else
    # Linux - use /usr/local/bin
    BIN_DIR="/usr/local/bin"
fi

# Create symlink
if [[ "$OSTYPE" == "darwin"* ]]; then
    ln -sf "$INSTALL_DIR/vocab-docker" "$BIN_DIR/vocab"
    print_success "Created 'vocab' command in ~/bin"
else
    if [ -w "$BIN_DIR" ]; then
        ln -sf "$INSTALL_DIR/vocab-docker" "$BIN_DIR/vocab"
        print_success "Created 'vocab' command in $BIN_DIR"
    else
        echo "We need sudo access to create the vocab command..."
        if sudo ln -sf "$INSTALL_DIR/vocab-docker" "$BIN_DIR/vocab"; then
            print_success "Created 'vocab' command in $BIN_DIR"
        else
            print_error "Failed to create vocab command. You can still use: ./vocab-docker"
        fi
    fi
fi

echo
echo -e "${GREEN}${BOLD}Installation completed successfully!${NC}"
echo
if [[ "$OSTYPE" == "darwin"* ]] && ! [[ ":$PATH:" == *":$HOME/bin:"* ]]; then
    echo "To complete the installation:"
    echo -e "${BOLD}source ~/.zshrc${NC}"
    echo
fi
echo "To start the vocabulary learning tool, simply run:"
echo -e "${BOLD}vocab${NC}"
echo
echo "Your data will be stored in:"
echo "- $DATA_DIR/data/ (vocabulary and progress)"
echo "- $DATA_DIR/firebase/ (credentials)"
echo "- $DATA_DIR/.env (configuration)" 