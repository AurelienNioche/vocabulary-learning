#!/bin/zsh

# Add Homebrew paths explicitly
export PATH="/opt/homebrew/bin:$PATH"

# Change to frontend directory
cd "$(dirname "$0")/../frontend" || exit 1

# Run ESLint
/opt/homebrew/bin/npm run lint 