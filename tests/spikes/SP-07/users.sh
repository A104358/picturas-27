#!/usr/bin/env sh
# Run inside the broker as the rabbitmq user (docker compose exec -u rabbitmq rabbitmq sh users.sh).
# Running rabbitmqctl as root before the server starts creates a root-owned .erlang.cookie and breaks boot.
rabbitmqctl -q add_user admin_spike admin-spike-pw-0123456789
rabbitmqctl -q set_user_tags admin_spike administrator
rabbitmqctl -q set_permissions admin_spike ".*" ".*" ".*"
# Worker: no configure (passive declares only), write only to the topic exchange, read only its queue.
rabbitmqctl -q add_user brightness_tool brightness-pw-0123456789
rabbitmqctl -q set_permissions brightness_tool "^$" "^picturas_topic$" "^brightness_queue$"
rabbitmqctl -q set_topic_permissions brightness_tool picturas_topic "^project_queue$" "^$"
rabbitmqctl -q add_user projects_svc projects-pw-0123456789
rabbitmqctl -q set_permissions projects_svc "^$" "^picturas(_topic)?$" "^project_queue$"
