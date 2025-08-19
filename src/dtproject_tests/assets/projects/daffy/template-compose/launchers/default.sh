#!/bin/bash

source /environment.sh

# initialize launch file
dt-launchfile-init

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------

# Configure your project here

# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE

# run compose entrypoint
dt-exec /compose-entrypoint.sh

# wait for app to end
dt-launchfile-join
