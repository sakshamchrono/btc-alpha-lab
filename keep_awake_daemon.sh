#!/bin/bash
while true; do
    openclaw message send --target "telegram:1792750225" --message "[System Message] Triggering background visual scraper check..."
    sleep 600
done
