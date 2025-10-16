# -*- coding: utf-8 -*-
import discord
import asyncio
import time
import os
from discord.ext import commands


################ Functions ################
##########################################
async def leave(bot, server_num, ui_manager, server_list):
    """음성 채널에서 나가기"""
    # UI 정리
    if ui_manager:
        await ui_manager.cleanup_ui(server_num)
    
    if server_num < len(server_list):
        server_list.pop(server_num)
    
    if server_num < len(bot.voice_clients):
        await bot.voice_clients[server_num].disconnect()

def server_check(bot, channel: discord.VoiceChannel):
    """서버 번호 찾기"""
    for server_num in range(len(bot.voice_clients)):
        try:
            if bot.voice_clients[server_num].channel == channel:
                return server_num
        except (IndexError, AttributeError):
            continue
    return None

class FakeCtx:
    """슬래시 명령어를 위한 가상 Context 클래스"""
    def __init__(self, interaction):
        self.author = interaction.user
        self.channel = interaction.channel
        self.guild = interaction.guild
        self.interaction = interaction
        self._voice_client = None
        
    @property
    def voice_client(self):
        return self._voice_client
        
    @voice_client.setter
    def voice_client(self, value):
        self._voice_client = value
        
    async def reply(self, message=None, embed=None, delete_after=None, ephemeral=True):
        if embed:
            if delete_after:
                await self.interaction.followup.send(embed=embed, ephemeral=ephemeral, delete_after=delete_after)
            else:
                await self.interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            if delete_after:
                await self.interaction.followup.send(message, ephemeral=ephemeral, delete_after=delete_after)
            else:
                await self.interaction.followup.send(message, ephemeral=ephemeral)
            
    async def send(self, content=None, embed=None, view=None, file=None, ephemeral=False):
        if embed and view and file:
             await self.interaction.followup.send(embed=embed, view=view, file=file, ephemeral=ephemeral)
        elif embed and view:
             await self.interaction.followup.send(embed=embed, view=view, ephemeral=ephemeral)
        elif embed:
             await self.interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
             await self.interaction.followup.send(content, ephemeral=ephemeral)
                
    def __getattr__(self, name):
        return getattr(self.interaction, name)

async def setup(bot):
    """Libs 모듈을 위한 setup 함수 (Cog가 아니므로 빈 함수)"""
    pass
