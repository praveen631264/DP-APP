import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatMessage } from '../services/chat.service';
import { SocketIOService } from '../services/socket-io.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-chat-panel',
  templateUrl: './chat-panel.component.html',
  styleUrls: ['./chat-panel.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule],
})
export class ChatPanelComponent implements OnInit, OnDestroy {

  @Input() chatMode: 'global' | 'document' = 'global';
  @Input() documentId: string | null = null;

  public messages: ChatMessage[] = [];
  public newMessage = '';
  private socketSubscription: Subscription | undefined;

  constructor(
    private chatService: ChatService,
    private socketService: SocketIOService
  ) { }

  ngOnInit(): void {
    if (this.chatMode === 'global') {
      this.socketService.connect();
      const sid = this.socketService.getSid();
      if (sid) {
        this.socketSubscription = this.socketService.on('chat_response').subscribe(message => {
          this.messages.push(message);
        });
      }
    }
  }

  ngOnDestroy(): void {
    if (this.chatMode === 'global') {
      this.socketService.disconnect();
      if (this.socketSubscription) {
        this.socketSubscription.unsubscribe();
      }
    }
  }

  sendMessage(): void {
    if (this.newMessage.trim() === '') {
      return;
    }

    const userMessage: ChatMessage = {
      sender: 'user',
      text: this.newMessage,
      timestamp: new Date().toISOString()
    };
    this.messages.push(userMessage);

    if (this.chatMode === 'global') {
      const sid = this.socketService.getSid();
      if (sid) {
        this.chatService.sendGlobalMessage(this.newMessage, sid).subscribe();
      }
    } else if (this.documentId) {
      this.chatService.sendDocumentMessage(this.newMessage, this.documentId).subscribe(aiMessage => {
        this.messages.push(aiMessage);
      });
    }

    this.newMessage = '';
  }
}