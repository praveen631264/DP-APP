import { Component, Input, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Document } from '../../services/document.service';
import { ChatService, ChatMessage } from '../../services/chat.service';

@Component({
  selector: 'app-chat-panel',
  templateUrl: './chat-panel.component.html',
  styleUrls: ['./chat-panel.component.scss']
})
export class ChatPanelComponent implements AfterViewChecked {
  @Input() document: Document | null = null;
  @ViewChild('messageContainer') private messageContainer!: ElementRef;

  messages: ChatMessage[] = [];
  chatForm: FormGroup;
  isAwaitingResponse = false;

  constructor(private fb: FormBuilder, private chatService: ChatService) {
    this.chatForm = this.fb.group({
      message: ['', Validators.required]
    });
    this.messages.push({ sender: 'ai', text: 'Hello! How can I help you with this document?', timestamp: new Date() });
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  sendMessage(): void {
    if (this.chatForm.invalid || !this.document) {
      return;
    }

    const userMessageText = this.chatForm.value.message;
    const userMessage: ChatMessage = {
      sender: 'user',
      text: userMessageText,
      timestamp: new Date()
    };
    this.messages.push(userMessage);

    this.isAwaitingResponse = true;
    this.chatForm.reset();

    this.chatService.sendMessage(this.document._id, userMessageText).subscribe(aiResponse => {
      this.messages.push(aiResponse);
      this.isAwaitingResponse = false;
    });
  }

  private scrollToBottom(): void {
    try {
      this.messageContainer.nativeElement.scrollTop = this.messageContainer.nativeElement.scrollHeight;
    } catch (err) {
      // Handle potential errors if the element isn't ready
    }
  }
}