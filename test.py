#!/usr/bin/python3
import lapis.db
import lapis.config as config
import lapis.logger as logger
import lapis.api as api
import datetime
import lapis.util as util
import random


test_build: dict = {
    # unique id
    "id": random.randint(0, 1000000),
    "name": "Test Build",
    "description": "This is a test build",
    "source": "/dev/null",
    "status": "pending",
    "started_at": util.timestamp,
    "finished_at": util.timestamp,
    "duration": 0,
    "output": {
        "stdout": "",
        "stderr": "",
    }
}

lapis.db.build.insert(test_build)
print(test_build)
print(lapis.db.build.status(test_build["id"]))

lapis.db.tasks.insert({
    "id": test_build["id"],
    "build_id": test_build["id"],
    "status": "pending",
    "started_at": util.timestamp,
    "finished_at": None,
    "duration": None,
    "type": "mock",
    "payload": {
        "command": "test"
    }
})

print(lapis.db.tasks.get(test_build["id"]))