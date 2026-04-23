import unittest
from pathlib import Path
import os

class TestContainerIntegrity(unittest.TestCase):

    def test_dockerfile_exists_and_valid(self):
        dockerfile = Path("Dockerfile")
        self.assertTrue(dockerfile.exists())
        content = dockerfile.read_text()
        self.assertIn("FROM python:3.11-slim", content)
        self.assertIn("ENTRYPOINT", content)
        self.assertIn("bandit", content)

    def test_docker_compose_exists_and_valid(self):
        compose = Path("docker-compose.yml")
        self.assertTrue(compose.exists())
        content = compose.read_text()
        self.assertIn("services:", content)
        self.assertIn("orchestrator:", content)
        self.assertIn("host.docker.internal", content)

if __name__ == '__main__':
    unittest.main()
