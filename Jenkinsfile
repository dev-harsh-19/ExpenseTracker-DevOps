
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'expensetracker:latest'
        CONTAINER_NAME = 'expensetracker'
        DATA_VOLUME = 'expensetracker-data'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '.venv/bin/python -m pytest -q'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t "$IMAGE_NAME" .'
            }
        }

        stage('Stop Old Container') {
            steps {
                sh '''
                    if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
                        docker rm --force "$CONTAINER_NAME"
                    fi
                '''
            }
        }

        stage('Deploy Application') {
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
                            "$IMAGE_NAME"
                    '''
                }
            }
        }
    }
}
