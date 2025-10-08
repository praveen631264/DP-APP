import { Component } from '@angular/core';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../chat.service';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.html',
  styleUrls: ['./chat.scss'],
  standalone: true,
  imports: [HttpClientModule, ReactiveFormsModule, CommonModule]
})
export class ChatComponent {
  correctionForm: FormGroup;
  globalChatForm: FormGroup;
  categoryChatForm: FormGroup;
  useMockData = false;

  constructor(private chatService: ChatService, private fb: FormBuilder) {
    this.correctionForm = this.fb.group({
      docId: [''],
      key: [''],
      value: ['']
    });

    this.globalChatForm = this.fb.group({
      message: ['']
    });

    this.categoryChatForm = this.fb.group({
      category: [''],
      message: ['']
    });
  }

  sendCorrection() {
    if (this.correctionForm.valid) {
      this.chatService.sendCorrection(this.correctionForm.value)
        .subscribe(response => {
          console.log('Correction sent:', response);
        });
    }
  }

  sendGlobalMessage() {
    if (this.globalChatForm.valid) {
      this.chatService.sendGlobalMessage(this.globalChatForm.value)
        .subscribe(response => {
          console.log('Global message sent:', response);
        });
    }
  }

  sendCategoryMessage() {
    if (this.categoryChatForm.valid) {
      this.chatService.sendCategoryMessage(this.categoryChatForm.value)
        .subscribe(response => {
          console.log('Category message sent:', response);
        });
    }
  }

  toggleMockData(event: any) {
    this.useMockData = event.target.checked;
    this.chatService.setUseMock(this.useMockData);
  }
}
