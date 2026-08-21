def logs(list_logs):
    failed_logs = []
    for line in list_logs:
        part = line.split("")
        user_name = part[0]
        status = part[1].split(":")[1]

        if status == "failed":
            failed_logs.append(user_name)
    return   failed_logs      