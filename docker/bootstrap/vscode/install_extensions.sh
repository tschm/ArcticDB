#!/bin/bash
# To be run INSIDE THE CONTAINER!

# Expects the following extensions in /scratch/data/vscode:
# ms-python.python-2022.21.13501006.vsix		
# ms-vscode.cmake-tools-1.13.29.vsix		
# ms-vscode.cpptools-1.13.8@linux-x64.vsix	
# twxs.cmake-0.0.17.vsix

code --install-extension /scratch/data/vscode/twxs.cmake-0.0.17.vsix
code --install-extension /scratch/data/vscode/ms-vscode.cpptools-1.13.8@linux-x64.vsix
code --install-extension /scratch/data/vscode/ms-python.python-2022.4.1.vsix
code --install-extension /scratch/data/vscode/ms-vscode.cmake-tools-1.13.29.vsix