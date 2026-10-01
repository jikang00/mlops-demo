pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'docker build -t frontend -f frontend/Dockerfile frontend'
            }
        }

        stage('Check') {
            steps {
                sh 'docker run --rm frontend echo success-frontend'
            }
        }
    }
}
