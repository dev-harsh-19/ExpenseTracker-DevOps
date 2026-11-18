pipeline {
    agent any

    environment {
        // Replace with your Docker Hub username/repository before creating the job.
        IMAGE_NAME = 'your-dockerhub-username/expensetracker'
        CONTAINER_NAME = 'expensetracker'
        DATA_VOLUME = 'expensetracker-data'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '.venv/bin/python -m pytest -q'
            }
        }

        stage('Build Docker image') {
            steps {
                sh 'docker build -t "$IMAGE_NAME:latest" .'
            }
        }

        stage('Push image to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKERHUB_USERNAME',
                    passwordVariable: 'DOCKERHUB_TOKEN'
                )]) {
                    sh '''
                        echo "$DOCKERHUB_TOKEN" | docker login \
                            --username "$DOCKERHUB_USERNAME" --password-stdin
                        docker push "$IMAGE_NAME:latest"
                        docker logout
                    '''
                }
            }
        }

        stage('Stop and remove old container') {
            steps {
                sh '''
                    if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
                        docker rm --force "$CONTAINER_NAME"
                    fi
                '''
            }
        }

        stage('Pull latest image') {
            steps {
                sh 'docker pull "$IMAGE_NAME:latest"'
            }
        }

        stage('Deploy updated container') {
            steps {
                withCredentials([string(
                    credentialsId: 'expense-flask-secret-key',
                    variable: 'FLASK_SECRET_KEY'
                )]) {
                    sh '''
                        docker run --detach \
                            --name "$CONTAINER_NAME" \
                            --restart unless-stopped \
                            --publish 5000:5000 \
                            --volume "$DATA_VOLUME:/data" \
                            --env SECRET_KEY="$FLASK_SECRET_KEY" \
                            "$IMAGE_NAME:latest"
                    '''
                }
            }
        }
    }
}
