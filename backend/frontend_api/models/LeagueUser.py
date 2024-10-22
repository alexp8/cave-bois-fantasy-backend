import json


class LeagueUser:
    def __init__(self, user_id: str, user_name: str, roster_avatar: str, user_avatar: str, roster_id: int):
        self.user_id = user_id
        self.user_name = user_name
        self.roster_avatar = roster_avatar
        self.user_avatar = user_avatar
        self.roster_id = roster_id

    def __repr__(self):
        return (
            f"LeagueUser(user_id={self.user_id}, "
            f"display_name='{self.user_name}', "
            f"roster_id='{self.roster_id}', "
            f"user_avatar='{self.user_avatar}', "
            f"roster_avatar='{self.roster_avatar}')"
        )

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'roster_avatar': self.roster_avatar,
            'user_avatar': self.user_avatar,
            'roster_id': self.roster_id
        }


def from_json(data: dict) -> LeagueUser:
    return LeagueUser(
        user_id=data['user_id'],
        user_name=data['user_name'],
        roster_avatar=data['roster_avatar'],
        user_avatar=data['user_avatar'],
        roster_id=data['roster_id']
    )


def get_user_with_roster_id(league_users: list[LeagueUser], roster_id: int) -> LeagueUser:
    """
        Get the user from the league_users list based on the given roster_id_temp.

        Args:
            league_users (list): List of users in the league.
            roster_id (int): The roster ID to find the user.

        Returns:
            user: The user with the matching roster_id or None if not found.
        """

    league_user: LeagueUser = next((user for user in league_users if user.roster_id == roster_id), None)

    if not league_user:
        raise ValueError(f"No user found with roster_id: {roster_id}")

    return league_user

def to_json(league_users: list[LeagueUser]) -> json:
    return [user.to_dict() for user in league_users]