import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-ai-agent-dialog',
  templateUrl: './ai-agent-dialog.component.html',
  styleUrls: ['./ai-agent-dialog.component.scss'],
  standalone: true,
  imports: [CommonModule, MatDialogModule, FormsModule]
})
export class AiAgentDialogComponent {

  messages: any[] = [];
  userInput: string = '';

  constructor(
    public dialogRef: MatDialogRef<AiAgentDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any) {
      this.messages.push({ sender: 'ai', text: `Hi, I am your AI assistant. I see that process '${this.data.process.name}' has failed. How can I help you?` });
    }

  sendMessage(): void {
    if (this.userInput.trim()) {
      this.messages.push({ sender: 'user', text: this.userInput });
      this.getAiResponse(this.userInput);
      this.userInput = '';
    }
  }

  getAiResponse(question: string): void {
    // Simulate AI response
    setTimeout(() => {
      let response = 'I am not sure how to help with that.';
      if (question.toLowerCase().includes('log')) {
        response = `Here are the logs for the failed process:\n\n${this.data.process.logs}`;
      } else if (question.toLowerCase().includes('cause')) {
        response = 'The failure was caused by a null pointer exception in the data validation step.';
      } else if (question.toLowerCase().includes('fix')) {
        response = 'To fix this issue, you need to add a null check before accessing the data. I can provide a code snippet if you like.';
      }
      this.messages.push({ sender: 'ai', text: response });
    }, 1000);
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

}
