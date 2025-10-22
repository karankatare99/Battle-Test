#!/bin/bash
# install_dependencies.sh - Install required dependencies for the Pokemon bot

echo "Installing dependencies for Pokemon Showdown Bot..."

# Install Python dependencies
pip3 install -r requirements.txt

# Check if psutil was installed successfully
python3 -c "import psutil; print('✅ psutil installed successfully')" 2>/dev/null || echo "⚠️ psutil installation failed, bot will use basic session cleanup"

echo "✅ Dependencies installation complete!"
echo ""
echo "Next steps:"
echo "1. Create a .env file with your bot credentials"
echo "2. Ensure kanto_data.json and moves.json are present"
echo "3. Start MongoDB if using local database"
echo "4. Run: python3 bot.py"
