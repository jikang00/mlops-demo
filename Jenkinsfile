pipeline{
  agent any
  stages{
    stage ('build'){
      steps{ sh 'docker build -t frontendtest ./frontend' }
    }

    stage ('test'){
      steps{ sh 'docker run --rm frontendtest echo hello' }
    }
    
    stage ('publish'){
      steps{
        script{
           docker.withRegistry('https://myregistry.com','registry-auth'){
               myapp = docker.build("myregistry.com/frontend:test", "./frontend")
               myapp.push()
           }
        }
      }
    }
  }
}
