// Runs once on an empty data dir (docker-entrypoint-initdb.d), as the root user.
const p = db.getSiblingDB("projects");
p.createUser({ user: "projects_svc", pwd: "projects-svc-pw-0123456789", roles: [{ role: "readWrite", db: "projects" }] });
p.createUser({ user: "backup_ro", pwd: "backup-ro-pw-0123456789", roles: [{ role: "read", db: "projects" }] });
p.project.insertOne({ _id: "fixture-1", name: "fixture", user_id: "u1" });
