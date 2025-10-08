import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { mockChatService } from './mock-data';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private useMock = false;

  constructor(private http: HttpClient) { }

  setUseMock(useMock: boolean) {
    this.useMock = useMock;
  }

  sendCorrection(correction: any) {
    if (this.useMock) {
      return mockChatService.sendCorrection(correction);
    }
    return this.http.post('/api/v1/chat/correct', correction);
  }

  sendGlobalMessage(message: any) {
    if (this.useMock) {
      return mockChatService.sendGlobalMessage(message);
    }
    return this.http.post('/api/v1/chat/global', message);
  }

  sendCategoryMessage(message: any) {
    if (this.useMock) {
      return mockChatService.sendCategoryMessage(message);
    }
    return this.http.post('/api/v1/chat/category', message);
  }
}
