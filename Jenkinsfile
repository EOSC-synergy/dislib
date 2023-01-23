@Library(['github.com/indigo-dc/jenkins-pipeline-library@release/2.2.0']) _

def projectConfig

pipeline {
    agent any

    stages {
        stage('JePL demo: hadolint') {
            when {
                anyOf {
                    branch 'feature/jepl_example'
                    changeRequest id: 'feature/jepl_example'
                    //buildingTag()
                }
            }
            steps {
                script {
                    projectConfig = pipelineConfig(
                        configFile: './.sqa/config_hadolint.yaml',
                        scmConfigs: [ localBranch: true ]
                    )
                    buildStages(projectConfig)
                }
            }
            post {
                cleanup {
                    cleanWs()
                }
            }
        }
    }
}
