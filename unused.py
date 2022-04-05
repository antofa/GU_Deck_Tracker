import os
import psutil

# set the base path of the freezed executable; (might change,
# check the last part for different architectures and python versions
basePath = 'd:/work/GU_Deck_Tracker/build/exe.win-amd64-3.10/'
# look for current processes and break when my program is found;
# be sure that the name is unique
for procId in psutil.pids():
    proc = psutil.Process(procId)
    if proc.name().lower() == 'GU_Deck_Tracker_a4.0.2.exe':
        break

# search for its dependencies and build a list of those *inside*
# its path, ignoring system deps in C:\Windows, etc.
deps = [p.path.lower() for p in proc.memory_maps() if p.path.lower().startswith(basePath)]

# create a list of all files inside the build path
allFiles = []
for root, dirs, files in os.walk(basePath):
    for fileName in files:
        filePath = os.path.join(root, fileName).lower()
        allFiles.append(filePath)

# create a list of existing files not required, ignoring .pyc and .pyd files
unusedSet = set(allFiles) ^ set(deps)
unusedFiles = []
for filePath in sorted(unusedSet):
    if filePath.endswith('pyc') or filePath.endswith('pyd'):
        continue
    unusedFiles.append((filePath[len(basePath):], os.stat(filePath).st_size))

# print the list, sorted by size
for filePath, size in sorted(unusedFiles, key=lambda d: d[1]):
    if (size > 1000000):
        print(filePath, size)
        # os.remove(f'{basePath}{filePath}')
