import asyncio
import uuid

from unittest.mock import MagicMock

from jupyter_nbmodel_client import BaseNbAgent, NbModelClient


async def test_default_content(ws_server):
    room = uuid.uuid4().hex
    with BaseNbAgent(f"{ws_server}/{room}") as agent:
        default_content = agent.as_dict()

    assert default_content == {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}


async def test_set_user_prompt(ws_server):
    room = uuid.uuid4().hex
    room_url = f"{ws_server}/{room}"
    with NbModelClient(room_url) as client:
        with BaseNbAgent(room_url) as agent:
            agent._on_user_prompt = MagicMock()
            idx = client.add_code_cell("print('hello')")
            client.set_cell_metadata(
                idx,
                "datalayer",
                {"ai": {"prompts": [{"id": "12345", "prompt": "Once upon a time"}]}},
            )

            await asyncio.sleep(0.1)

            assert agent.as_dict() == {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {
                            "datalayer": {
                                "ai": {"prompts": [{"id": "12345", "prompt": "Once upon a time"}]}
                            }
                        },
                        "outputs": [],
                        "source": "print('hello')",
                        "id": client[idx]["id"],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }

            assert agent._on_user_prompt.called
            args, kwargs = agent._on_user_prompt.call_args
            assert args == (client[idx]["id"], "Once upon a time")
            assert kwargs == {}


async def test_set_cell_with_user_prompt(ws_server):
    room = uuid.uuid4().hex
    room_url = f"{ws_server}/{room}"
    with NbModelClient(room_url) as client:
        with BaseNbAgent(room_url) as agent:
            agent._on_user_prompt = MagicMock()
            client.add_code_cell(
                "print('hello')",
                metadata={
                    "datalayer": {
                        "ai": {"prompts": [{"id": "12345", "prompt": "Once upon a time"}]}
                    }
                },
            )

            await asyncio.sleep(0.1)

            assert agent.as_dict() == {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {
                            "datalayer": {
                                "ai": {"prompts": [{"id": "12345", "prompt": "Once upon a time"}]}
                            }
                        },
                        "outputs": [],
                        "source": "print('hello')",
                        "id": client[0]["id"],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }

            assert agent._on_user_prompt.called
            args, kwargs = agent._on_user_prompt.call_args
            assert args == (client[0]["id"], "Once upon a time")
            assert kwargs == {}
