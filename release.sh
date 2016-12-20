#!/bin/bash
OUTPUT=$(python build/package_workflow.py . -o build/)


TEXT_ARRRAY=($OUTPUT)

#Title of Workflow
echo ${TEXT_ARRRAY[0]}

# Workflwo File output name
echo ${TEXT_ARRRAY[1]}

# Version
echo ${TEXT_ARRRAY[2]}

echo "     ________                               __   _______ __ "
echo "    / ____/ /_  ____ _____  ____ ____  ____/ /  / ____(_) /__  _____ "
echo "   / /   / __ \/ __ \`/ __ \/ __ \`/ _ \/ __  /  / /_  / / / _ \/ ___/ "
echo "  / /___/ / / / /_/ / / / / /_/ /  __/ /_/ /  / __/ / / /  __(__  ) "
echo "  \____/_/ /_/\__,_/_/ /_/\__, /\___/\__,_/  /_/   /_/_/\___/____/ "
echo "                         /____/ "
echo ""

git status -s

echo " Commit and make a release?"

read -p "Are you sure? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    # do dangerous stuff

    git add -u
    git commit -m "Prepping release ${TEXT_ARRRAY[2]}"
    git push

    python release.py ${TEXT_ARRRAY[2]} ${TEXT_ARRRAY[1]}
fi