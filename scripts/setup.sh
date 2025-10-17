#!/bin/bash

set -e

# Detect architecture
ARCH=$(uname -m)

if [ "$ARCH" = "x86_64" ]; then
    TAIDL_IMAGE_NAME="devanshdvj/taidl-micro25-artifact:amd64"
    BASELINE_IMAGE_NAME="devanshdvj/taidl-micro25-artifact:baseline-amd64"

    TAIDL_IMAGE_TARGZ="taidl-micro25-artifact-amd64.tar.gz"
    BASELINE_IMAGE_TARGZ="taidl-micro25-artifact-baseline-amd64.tar.gz"

    TAIDL_BUILD_FOLDER="artifact-taidl"
    BASELINE_BUILD_FOLDER="artifact-baseline"
elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    TAIDL_IMAGE_NAME="devanshdvj/taidl-micro25-artifact:arm64"
    BASELINE_IMAGE_NAME=""

    TAIDL_IMAGE_TARGZ="taidl-micro25-artifact-arm64.tar.gz"
    BASELINE_IMAGE_TARGZ=""

    TAIDL_BUILD_FOLDER="artifact-taidl"
    BASELINE_BUILD_FOLDER=""
else
    echo "Error: Unsupported architecture: $ARCH"
    exit 1
fi

cd "$(dirname "$0")/../"
REPO_DIR="$(pwd)"

if [[ "$1" == "--build" ]]; then
    echo "Warning: Building Docker images locally is not recommended unless you have a machine with good internet connectivity and sufficient resources."
    echo "Proceeding with local build of Docker images."

    # Build TAIDL image
    echo
    $REPO_DIR/$TAIDL_BUILD_FOLDER/build.sh

    # Build Baseline image (only for amd64)
    if [[ "$BASELINE_BUILD_FOLDER" != "" ]]; then
        echo
        $REPO_DIR/$BASELINE_BUILD_FOLDER/build.sh
    fi

    # Clean up dangling images
    echo
    echo "Cleaning up dangling Docker images..."
    docker image prune -f

    exit 0
fi

if ! docker image inspect "$TAIDL_IMAGE_NAME" >/dev/null 2>&1; then
    # Load TAIDL image
    echo
    echo "Searching for $TAIDL_IMAGE_TARGZ in $REPO_DIR and its parent directory."
    if [[ -f "$REPO_DIR/$TAIDL_IMAGE_TARGZ" ]]; then
        echo
        echo "Found $REPO_DIR/$TAIDL_IMAGE_TARGZ. Loading..."
        docker load -i "$REPO_DIR/$TAIDL_IMAGE_TARGZ"
    elif [[ -f "$REPO_DIR/../$TAIDL_IMAGE_TARGZ" ]]; then
        echo
        echo "Found $REPO_DIR/../$TAIDL_IMAGE_TARGZ. Loading..."
        docker load -i "$REPO_DIR/../$TAIDL_IMAGE_TARGZ"
    else
        echo
        echo "Info: $TAIDL_IMAGE_TARGZ not found locally in $REPO_DIR or its parent directory."
        echo "Attempting to pull from Docker Hub instead."

        docker pull $TAIDL_IMAGE_NAME || {
            echo "Error: Failed to pull $TAIDL_IMAGE_NAME from Docker Hub."
            echo "This may be due to network issues or the image may have been removed from Docker Hub."
            echo
            echo "Please download the appropriate image tarball from https://zenodo.org/records/16971223 and place it in $REPO_DIR or its parent directory."
            exit 1
        }
    fi

    # Clean up dangling images
    echo
    echo "Cleaning up dangling Docker images..."
    docker image prune -f
fi

if [[ "$BASELINE_IMAGE_NAME" != "" ]] && ! docker image inspect "$BASELINE_IMAGE_NAME" >/dev/null 2>&1; then
    # Load Baseline image (only for amd64)
    echo
    echo "Searching for $BASELINE_IMAGE_TARGZ in $REPO_DIR and its parent directory."
    if [[ -f "$REPO_DIR/$BASELINE_IMAGE_TARGZ" ]]; then
        echo
        echo "Found $REPO_DIR/$BASELINE_IMAGE_TARGZ. Loading..."
        docker load -i "$REPO_DIR/$BASELINE_IMAGE_TARGZ"
    elif [[ -f "$REPO_DIR/../$BASELINE_IMAGE_TARGZ" ]]; then
        echo
        echo "Found $REPO_DIR/../$BASELINE_IMAGE_TARGZ. Loading..."
        docker load -i "$REPO_DIR/../$BASELINE_IMAGE_TARGZ"
    else
        echo
        echo "Info: $BASELINE_IMAGE_TARGZ not found locally in $REPO_DIR or its parent directory."
        echo "Attempting to pull from Docker Hub instead."

        docker pull $BASELINE_IMAGE_NAME || {
            echo "Error: Failed to pull $BASELINE_IMAGE_NAME from Docker Hub."
            echo "This may be due to network issues or the image may have been removed from Docker Hub."
            echo
            echo "Please download the appropriate image tarball from https://zenodo.org/records/16971223 and place it in $REPO_DIR or its parent directory."
            exit 1
        }
    fi


    # Clean up dangling images
    echo
    echo "Cleaning up dangling Docker images..."
    docker image prune -f
fi
