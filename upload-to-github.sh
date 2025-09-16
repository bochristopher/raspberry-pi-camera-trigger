#!/usr/bin/env bash
set -euo pipefail

# ====== Edit only if your GitHub username is different ======
GITHUB_USER="bochristopher"
GITHUB_EMAIL="bochristopher.engineer@protonmail.com"
REPO_NAME="raspberry-pi-camera-trigger"
REPO_SSH="git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
# ============================================================

echo "==> Installing git and SSH client"
sudo apt update -y
sudo apt install -y git openssh-client

echo "==> Configuring git identity"
git config --global user.name "Bo Christopher"
git config --global user.email "${GITHUB_EMAIL}"

echo "==> Generating SSH key (ed25519) if missing"
mkdir -p ~/.ssh
if [ ! -f ~/.ssh/id_ed25519 ]; then
  ssh-keygen -t ed25519 -C "${GITHUB_EMAIL}" -f ~/.ssh/id_ed25519 -N ""
else
  echo "SSH key already exists at ~/.ssh/id_ed25519"
fi

echo "==> Starting ssh-agent and adding key"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

echo "==> Writing basic SSH config for GitHub (will append if already present)"
if ! grep -q "Host github.com" ~/.ssh/config 2>/dev/null; then
  cat <<'EOF' >> ~/.ssh/config
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
EOF
  chmod 600 ~/.ssh/config
else
  echo "Found existing ~/.ssh/config; leaving as is."
fi

echo "==> Public key below — copy it to GitHub: Settings -> SSH and GPG keys -> New SSH key"
echo "-----------------------------------------------------------------------"
cat ~/.ssh/id_ed25519.pub
echo "-----------------------------------------------------------------------"
echo "After adding the key on GitHub, press Enter to continue..."
read -r _

echo "==> Testing SSH connection to GitHub"
ssh -T git@github.com || true
echo "(If you saw 'Hi <username>! You've successfully authenticated', you're good.)"

echo "==> Using existing camera trigger system in current directory"
cd "$(dirname "$0")"

# Repository name is already correct in README - no changes needed

# Update remote to new repository name
if git remote get-url origin >/dev/null 2>&1; then
  echo "Updating remote origin to ${REPO_SSH}"
  git remote set-url origin "${REPO_SSH}"
else
  echo "Adding remote origin: ${REPO_SSH}"
  git remote add origin "${REPO_SSH}"
fi

echo "==> Current repository status:"
git status --short

echo "==> Creating GitHub repo (if it doesn't exist) – manual step if needed"
echo "If the remote repo doesn't exist yet, create it at: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo "Description: 'Production-ready Raspberry Pi camera trigger with secure provenance logging'"
echo "Make it PUBLIC and don't initialize with README/license/gitignore"
echo ""
echo "Press Enter to attempt push to GitHub..."
read -r _

echo "==> Pushing to GitHub..."
git push -u origin main

echo "✅ Done! Your production camera trigger system is now at:"
echo "    https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "Users can now install with:"
echo "    git clone git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
echo "    cd ${REPO_NAME}"
echo "    sudo ./scripts/setup.sh"
echo ""
echo "Test with dry-run mode:"
echo "    python main.py --dry-run --trigger-test"