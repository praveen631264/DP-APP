import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class TaskService {

  private tasks: any[] = [
    { id: 'celery-1', name: 'Celery Task 1', type: 'Celery', status: 'Running' },
    { id: 'celery-2', name: 'Celery Task 2', type: 'Celery', status: 'Pending' },
    { id: 'redis-1', name: 'Redis Task 1', type: 'Redis', status: 'Running' },
    { id: 'ai-1', name: 'AI Processing Task 1', type: 'AI', status: 'Running' },
    { id: 'ai-2', name: 'AI Processing Task 2', type: 'AI', status: 'Failed' },
  ];

  getTasks(): Observable<any[]> {
    return of(this.tasks);
  }

  stopTask(taskId: string): Observable<any> {
    const task = this.tasks.find(t => t.id === taskId);
    if (task) {
      task.status = 'Stopped';
    }
    return of(task);
  }

  restartTask(taskId: string): Observable<any> {
    const task = this.tasks.find(t => t.id === taskId);
    if (task) {
      task.status = 'Running';
    }
    return of(task);
  }
}
