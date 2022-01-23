class TarkovKill:
    def __init__(self, kill_id, killer, killed, guild, tag, time):
        self.kill_id = kill_id
        self.killer = killer
        self.killed = killed
        self.guild = guild
        self.tag = tag or "None"
        self.time = time

    def __str__(self):
        return f"[{self.kill_id}] {self.killer} killed {self.killed} [{self.tag}]"
