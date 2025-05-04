Session_service vs memory_service:
session_service is used to store the information of this particular session whereas memory_service is the long term memory, which maintains the memory of all the specified sessions.

One session constitutes of user_id, sesison_id and app_id. Session_id referes to the chat that you want to refer to.
Example:
session_service.create_session(
app_name="MealAssistant",
user_id="adi123",
session_id="morning_chat"
)

so when i say, : "Hi, my name is Ahaskar. What do you do?", the runner stores this in the session service with the reply "You are XYZ..." as well
now when i ask it the next question, it just adds this lump of information behind it and send to the base tool that is, it sees this:
[User]: Hi, my name is Ahaskar. What do you do?
[Agent]: You are XYZ...
[User]: What is my name?

so if i ask the information from the same session, it'll answer as it has all the information with it, the issue'll be when you go to the next session.

A good rule of thumb: use memory_service for long-term retention of important facts, and do not rely on session_service for memory between sessions. The session_service is best viewed as a temporary working memory for the current session only.
