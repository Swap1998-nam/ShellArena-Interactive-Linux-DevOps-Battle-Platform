pipeline {
  agent { label 'docker' }
  options {
    timestamps()
    timeout(time: 30, unit: 'MINUTES')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '15'))
  }
  parameters {
    booleanParam(name: 'RUN_SONAR', defaultValue: false, description: 'Requires SonarQube server, scanner tool, and webhook configured in Jenkins')
    booleanParam(name: 'PUBLISH_IMAGE', defaultValue: false, description: 'Push the tested image to the configured registry')
  }
  environment {
    // Configure these two values for your own registry. No credentials in Git.
    REGISTRY = 'ghcr.io'
    IMAGE_REPOSITORY = 'swap1998-nam/shellarena'
    IMAGE_TAG = "build-${BUILD_NUMBER}"
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Install & lint') {
      steps {
        sh '''
          python3 -m venv .venv
          .venv/bin/pip install -r requirements-dev.txt
          .venv/bin/ruff check backend tests scripts
          node --check frontend/app.js
        '''
      }
    }
    stage('Unit & API tests') {
      steps { sh '.venv/bin/pytest --cov=backend --cov-fail-under=88 --cov-report=xml --junitxml=reports/pytest.xml' }
      post { always { junit 'reports/pytest.xml' } }
    }
    stage('Security gates') {
      steps {
        sh '''
          .venv/bin/bandit -q -r backend -ll
          .venv/bin/pip-audit -r backend/requirements.txt
          trivy fs --scanners misconfig,secret --severity HIGH,CRITICAL --exit-code 1 .
        '''
      }
    }
    stage('Browser tests') {
      steps {
        sh '''
          npm ci --ignore-scripts
          npx playwright install chromium
          node tests/browser.cjs
        '''
      }
    }
    stage('SonarQube analysis') {
      when { expression { params.RUN_SONAR } }
      steps {
        script {
          def scannerHome = tool 'SonarScanner'
          withSonarQubeEnv('SonarQube') {
            sh "${scannerHome}/bin/sonar-scanner"
          }
        }
      }
    }
    stage('Quality gate') {
      when { expression { params.RUN_SONAR } }
      steps {
        timeout(time: 5, unit: 'MINUTES') { waitForQualityGate abortPipeline: true }
      }
    }
    stage('Build & inspect image') {
      steps {
        sh '''
          docker build --pull -t "$REGISTRY/$IMAGE_REPOSITORY:$IMAGE_TAG" .
          trivy image --severity HIGH,CRITICAL --exit-code 1 "$REGISTRY/$IMAGE_REPOSITORY:$IMAGE_TAG"
          trivy image --format cyclonedx --output sbom.cdx.json "$REGISTRY/$IMAGE_REPOSITORY:$IMAGE_TAG"
        '''
      }
    }
    stage('Publish approved artifact') {
      when { expression { params.PUBLISH_IMAGE } }
      steps {
        withCredentials([usernamePassword(credentialsId: 'container-registry', usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
          sh '''
            set +x
            export DOCKER_CONFIG="$(mktemp -d)"
            trap 'rm -rf "$DOCKER_CONFIG"' EXIT
            printf '%s' "$REG_PASS" | docker login "$REGISTRY" -u "$REG_USER" --password-stdin
            docker push "$REGISTRY/$IMAGE_REPOSITORY:$IMAGE_TAG"
          '''
        }
      }
    }
  }
  post {
    always { archiveArtifacts artifacts: 'coverage.xml,reports/**,test-results/**,sbom.cdx.json', allowEmptyArchive: true }
  }
}
