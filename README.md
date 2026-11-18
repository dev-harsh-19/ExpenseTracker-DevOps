# ExpenseTracker – DevOps-Based Expense Management System

A beginner-friendly expense dashboard built with Flask, SQLite, HTML, CSS, and JavaScript. The project includes Docker packaging and a Jenkins pipeline that builds, tests, publishes, and deploys the app to a single Ubuntu EC2 instance.

## What the app does

- Add an expense with its name, amount, category, and date.
- View recorded expenses and delete an entry.
- See total spending, transaction count, and spending grouped by category.
- Store records in SQLite so they persist between container updates.

The amount field does not assume a currency. Use one currency consistently for all entries. There is no login, payment integration, or external database.

## Project files

```text
ExpenseTracker/
├── app.py                    # Flask routes, input validation, and SQLite setup
├── requirements.txt          # Python packages used by the app and tests
├── Dockerfile                # Builds the container image
├── .dockerignore             # Keeps local files and database out of image builds
├── Jenkinsfile               # Jenkins build, test, publish, and deploy stages
├── .gitignore                # Excludes local environments and database files
├── README.md                 # Setup, usage, and deployment guide
├── database/
│   └── .gitkeep              # Keeps the empty database directory in Git
├── templates/
│   ├── index.html            # Dashboard, expense table, and category totals
│   └── add_expense.html      # Expense entry form
├── static/
│   ├── css/style.css         # Responsive dashboard styles
│   └── js/script.js          # Delete confirmation
└── tests/
    └── test_app.py           # Flask route and validation tests
```

## Run locally

You need Python 3.10 or later. Run these commands from the project directory.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python app.py
```

If PowerShell prevents environment activation, either allow it for the current terminal with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or run `.venv\Scripts\python.exe -m pip install -r requirements.txt`, `.venv\Scripts\python.exe -m pytest -q`, and `.venv\Scripts\python.exe app.py` without activating.

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python app.py
```

Open [http://localhost:5000](http://localhost:5000). The default SQLite file is created at `database/expenses.db`. Set `DATABASE_PATH` to use another location. Set `SECRET_KEY` to a private random value when using the app beyond local development; the built-in key is for local development only.

## Run with Docker

Install Docker Desktop (Windows/macOS) or Docker Engine (Linux), then run:

```bash
docker build -t expensetracker:local .
docker volume create expensetracker-data
docker run -d --name expensetracker \
  -p 5000:5000 \
  -v expensetracker-data:/data \
  -e SECRET_KEY="replace-with-a-private-random-value" \
  expensetracker:local
```

Visit [http://localhost:5000](http://localhost:5000). The named `expensetracker-data` Docker volume stores SQLite data at `/data/expenses.db`, so removing or replacing the container does not remove saved expenses.

Useful commands:

```bash
docker logs -f expensetracker
docker stop expensetracker
docker rm expensetracker
```

## Push the project to GitHub

1. Create an empty repository on GitHub (do not initialize it with a README if you already have this project README).
2. From this project directory, set up Git and make the first commit:

   ```bash
   git init
   git add .
   git commit -m "Create ExpenseTracker application"
   git branch -M main
   ```

3. Add your repository URL and push:

   ```bash
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/ExpenseTracker.git
   git push -u origin main
   ```

Replace `YOUR_GITHUB_USERNAME` with your GitHub account name. GitHub may ask you to authenticate using a browser or a personal access token; do not put credentials in the repository.

## Deploy to one Ubuntu EC2 instance

This setup runs Jenkins and the app's Docker container on the same VM. A `t3.medium` (4 GiB memory) or similar instance is a more comfortable starting point than a small instance because Jenkins and builds use memory. EC2, public IPv4, and data-transfer charges may apply.

### 1. Create the instance and security group

1. In AWS EC2, launch an Ubuntu Server 24.04 LTS instance.
2. Create or select a key pair and keep the downloaded private key safe.
3. In the instance security group, add inbound rules:
   - SSH, TCP 22, source **My IP**.
   - Custom TCP 8080 (Jenkins), source **My IP** only. Do not expose Jenkins to the whole internet.
   - Custom TCP 5000 (the app), source `0.0.0.0/0` (and `::/0` if using IPv6) if the app should be public.
4. Launch the instance and note its public IPv4 address. Use an Elastic IP if you need that address to remain stable across stop/start.

### 2. Install Java, Git, Docker, and Jenkins

Connect over SSH using the key pair and the instance's public IP. For example:

```bash
ssh -i /path/to/your-key.pem ubuntu@EC2_PUBLIC_IP
```

Install Java 17, Git, Docker, Python's virtual environment support, and Jenkins:

```bash
sudo apt update
sudo apt install -y fontconfig openjdk-17-jre git docker.io python3-venv curl
sudo systemctl enable --now docker

sudo install -d -m 0755 /etc/apt/keyrings
sudo curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key \
  -o /etc/apt/keyrings/jenkins-keyring.asc
echo "deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" \
  | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install -y jenkins
sudo systemctl enable --now jenkins
```

Allow the Jenkins service account to use Docker, then restart Jenkins:

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

The Docker group grants root-equivalent control of the instance. Only trusted Jenkins jobs and users should have access. Verify both services:

```bash
sudo systemctl status docker --no-pager
sudo systemctl status jenkins --no-pager
```

Open `http://EC2_PUBLIC_IP:8080` from the IP allowed in your security group. Get the first-time setup password on the instance with:

```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Complete Jenkins' setup wizard, install the suggested plugins, and create an administrator account. Keep Jenkins restricted to your IP; do not put credentials or the initial password in GitHub.

### 3. Configure Jenkins credentials and the image name

1. In Jenkins, open **Manage Jenkins → Credentials → System → Global credentials → Add Credentials**.
2. Add a **Username with password** credential:
   - Username: your Docker Hub username.
   - Password: a Docker Hub access token (use the token as the password).
   - ID: `dockerhub-credentials`.
3. Add a **Secret text** credential:
   - Secret: a long, randomly generated Flask secret key.
   - ID: `expense-flask-secret-key`.
4. In `Jenkinsfile`, replace `your-dockerhub-username/expensetracker` with your Docker Hub username and repository name. Commit and push that change to GitHub. Create the repository on Docker Hub first if needed.

Never put the Docker Hub token or Flask secret in the Jenkinsfile, source code, or GitHub.

### 4. Create and run a pipeline

1. From the Jenkins dashboard, select **New Item**, enter a job name, choose **Pipeline**, and select **OK**.
2. In the job configuration, under **Pipeline**, set **Definition** to **Pipeline script from SCM**.
3. Select **Git**, enter your GitHub repository URL, set the branch to `*/main`, and keep the script path as `Jenkinsfile`.
4. For a public GitHub repository, credentials can be left blank. For a private repository, add a GitHub access credential in Jenkins and select it here.
5. Save, then select **Build Now**. The pipeline checks out the code, installs Python dependencies, runs tests, builds the Docker image, pushes it to Docker Hub, replaces the old container, and starts the latest image.

For automatic builds, enable **Poll SCM** in the job (for example `H/5 * * * *`) or configure a GitHub webhook. A webhook requires network access to Jenkins; do not open Jenkins to everyone just to enable one.

The app is available at `http://EC2_PUBLIC_IP:5000`. SQLite data is stored in the `expensetracker-data` Docker volume and is retained across deployments. If a deployment fails after the old container is removed, fix the pipeline error and run the job again.

## Troubleshooting

- **Port 5000 is unreachable:** Confirm the instance is running, the security group allows inbound TCP 5000 from your address, and `docker ps` shows the app container. Check `docker logs expensetracker`.
- **Jenkins page is unreachable:** Confirm inbound TCP 8080 is limited to your current public IP, check `sudo systemctl status jenkins`, and review `sudo journalctl -u jenkins -n 100 --no-pager`.
- **Docker permission denied in Jenkins:** Check `id jenkins` includes the `docker` group, then run `sudo systemctl restart jenkins`. Review Docker socket permissions and Jenkins logs.
- **Pipeline cannot find Python or venv:** Install `python3` and `python3-venv` on the EC2 host, then rerun the build.
- **Docker Hub push is denied:** Check the `dockerhub-credentials` ID, token permissions, and that the image name in `Jenkinsfile` uses your Docker Hub namespace and repository.
- **Pipeline reports a missing credential:** Add a credential with the exact ID `dockerhub-credentials` or `expense-flask-secret-key` and the matching credential type.
- **Container name or port is already in use:** Check `docker ps -a` and `sudo ss -ltnp | grep ':5000'`. The pipeline removes its container named `expensetracker`; remove a conflicting container only after confirming it is safe to do so.
- **Expenses disappear:** Make sure the container was started with `-v expensetracker-data:/data` (the pipeline does this). Do not remove the named volume if you want to keep its data.
- **Tests fail locally:** Run `python -m pytest -q` from the project root and read the first failing assertion before deploying.
