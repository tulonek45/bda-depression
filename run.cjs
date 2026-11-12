const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SCRIPTS = {
  download_data: 'scripts/download_data.py',
};

const VENV_DIR = '.venv';

function runCommand(command, args = []) {
  const result = spawnSync(command, args, { stdio: 'inherit', shell: true });
  if (result.status !== 0) {
    console.error(`Error executing command: ${command}`);
    process.exit(result.status);
  }
}

function ensureEnvironment() {
  if (!fs.existsSync(VENV_DIR)) {
    console.log(`Creating virtual environment in '${VENV_DIR}'...`);
    const pyCmd = process.platform === 'win32' ? 'python' : 'python3';
    
    try {
      runCommand(pyCmd, ['-m', 'venv', VENV_DIR]);
    } catch (err) {
      runCommand('python', ['-m', 'venv', VENV_DIR]);
    }
  }

  const isWin = process.platform === 'win32';
  const venvPython = path.join(
    VENV_DIR,
    isWin ? 'Scripts' : 'bin',
    isWin ? 'python.exe' : 'python'
  );
  const pipExecutable = path.join(
    VENV_DIR,
    isWin ? 'Scripts' : 'bin',
    isWin ? 'pip.exe' : 'pip'
  );

  if (fs.existsSync('requirements.txt')) {
    const flagFile = path.join(VENV_DIR, '.installed_req');
    const reqStat = fs.statSync('requirements.txt');
    let needsInstall = true;

    if (fs.existsSync(flagFile)) {
      const flagStat = fs.statSync(flagFile);
      // If requirements.txt is older than or equal to the flag file, skip install
      if (reqStat.mtimeMs <= flagStat.mtimeMs) {
        needsInstall = false;
        console.log('Dependencies are up to date. Skipping pip install.');
      }
    }

    if (needsInstall) {
      console.log('Installing/updating dependencies...');
      runCommand(pipExecutable, ['install', '--upgrade', 'pip']);
      runCommand(pipExecutable, ['install', '-r', 'requirements.txt']);

      fs.writeFileSync(flagFile, '');
    }
  }

  return venvPython;
}

function main() {
  const args = process.argv.slice(2);
  const scriptName = args[0];

  if (!scriptName || !SCRIPTS[scriptName]) {
    console.error(`Error: Unknown or missing script name.`);
    console.error(`Available scripts: ${Object.keys(SCRIPTS).join(', ')}`);
    process.exit(1);
  }

  const venvPython = ensureEnvironment();
  const scriptPath = SCRIPTS[scriptName];
  const extraArgs = args.slice(1);

  runCommand(venvPython, [scriptPath, ...extraArgs]);
}

main();