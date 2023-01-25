@Library(['github.com/indigo-dc/jenkins-pipeline-library@release/2.2.0']) _

def projectConfig

pipeline {
    agent any

    stages {
        stage('JePL demo: hadolint') {
            when {
                anyOf {
                    branch 'feature/jepl_example'
                    branch 'fix/jepl_example'
                    branch 'test/multiple_configs'
                    changeRequest id: '7'
                    changeRequest id: '8'
                    changeRequest id: '9'
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
        stage('SQA baseline criterion: QC.Sec') {
            steps {
                script {
                    projectConfig = pipelineConfig(
                        configFile: '.sqa/config.yml',
                        scmConfigs: [ localBranch: true ],
                        validatorDockerImage: 'eoscsynergy/jpl-validator:2.4.0'
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
