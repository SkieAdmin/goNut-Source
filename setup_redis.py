#!/usr/bin/env python
"""
Auto-setup script for porn_redis Docker container
Checks if Docker is available and creates the Redis container if needed
"""
import subprocess
import sys
import time


def run_command(cmd, shell=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_docker():
    """Check if Docker is installed and running"""
    success, stdout, stderr = run_command("docker --version")
    if not success:
        print("❌ Docker is not installed or not in PATH")
        print("   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
        return False
    
    print(f"✓ Docker found: {stdout.strip()}")
    
    # Check if Docker daemon is running
    success, stdout, stderr = run_command("docker ps")
    if not success:
        print("❌ Docker daemon is not running")
        print("   Please start Docker Desktop")
        return False
    
    print("✓ Docker daemon is running")
    return True


def check_redis_container():
    """Check if porn_redis container exists"""
    success, stdout, stderr = run_command("docker ps -a --filter name=porn_redis --format {{.Names}}")
    return "porn_redis" in stdout


def check_redis_running():
    """Check if porn_redis container is running"""
    success, stdout, stderr = run_command("docker ps --filter name=porn_redis --format {{.Names}}")
    return "porn_redis" in stdout


def create_redis_container():
    """Create and start the porn_redis container using docker-compose"""
    print("\n🚀 Creating porn_redis container...")
    
    # Check if docker-compose.yml exists
    import os
    if not os.path.exists("docker-compose.yml"):
        print("❌ docker-compose.yml not found")
        return False
    
    # Start the container
    success, stdout, stderr = run_command("docker-compose up -d porn_redis")
    if not success:
        print(f"❌ Failed to create container: {stderr}")
        return False
    
    print("✓ Container created successfully")
    
    # Wait for Redis to be ready
    print("⏳ Waiting for Redis to be ready...")
    for i in range(10):
        time.sleep(1)
        success, stdout, stderr = run_command("docker exec porn_redis redis-cli ping")
        if success and "PONG" in stdout:
            print("✓ Redis is ready!")
            return True
        print(f"   Waiting... ({i+1}/10)")
    
    print("⚠️  Redis container started but not responding yet")
    return True


def start_redis_container():
    """Start existing porn_redis container"""
    print("\n▶️  Starting porn_redis container...")
    success, stdout, stderr = run_command("docker start porn_redis")
    if not success:
        print(f"❌ Failed to start container: {stderr}")
        return False
    
    print("✓ Container started successfully")
    
    # Wait for Redis to be ready
    time.sleep(2)
    success, stdout, stderr = run_command("docker exec porn_redis redis-cli ping")
    if success and "PONG" in stdout:
        print("✓ Redis is ready!")
    
    return True


def main():
    print("=" * 60)
    print("🔧 porn_redis Setup Script")
    print("=" * 60)
    
    # Check Docker
    if not check_docker():
        sys.exit(1)
    
    # Check if container exists
    if check_redis_container():
        if check_redis_running():
            print("\n✓ porn_redis is already running")
            
            # Test connection
            success, stdout, stderr = run_command("docker exec porn_redis redis-cli ping")
            if success and "PONG" in stdout:
                print("✓ Redis connection test successful")
            else:
                print("⚠️  Redis container is running but not responding")
        else:
            # Container exists but not running
            if not start_redis_container():
                sys.exit(1)
    else:
        # Container doesn't exist, create it
        if not create_redis_container():
            sys.exit(1)
    
    # Show container info
    print("\n" + "=" * 60)
    print("📊 Container Information:")
    print("=" * 60)
    run_command("docker ps --filter name=porn_redis --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    
    print("\n✅ Setup complete! Redis is available at localhost:6379")
    print("\nUseful commands:")
    print("  • View logs:    docker logs porn_redis")
    print("  • Stop Redis:   docker stop porn_redis")
    print("  • Start Redis:  docker start porn_redis")
    print("  • Redis CLI:    docker exec -it porn_redis redis-cli")


if __name__ == "__main__":
    main()
