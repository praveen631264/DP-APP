import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Playbook, PlaybookService } from '../services/playbook.service';

@Component({
  selector: 'app-playbook-list',
  templateUrl: './playbook-list.component.html',
  styleUrls: ['./playbook-list.component.scss'],
  standalone: true,
  imports: [CommonModule, RouterModule]
})
export class PlaybookListComponent implements OnInit {

  public playbooks: Playbook[] = [];

  constructor(
    private playbookService: PlaybookService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadPlaybooks();
  }

  loadPlaybooks(): void {
    this.playbookService.getPlaybooks().subscribe(data => {
      this.playbooks = data;
    });
  }

  createNewPlaybook(): void {
    this.router.navigate(['/playbooks/new']);
  }

  editPlaybook(id: string): void {
    this.router.navigate(['/playbooks', id, 'edit']);
  }

  deletePlaybook(id: string): void {
    if (confirm('Are you sure you want to delete this playbook?')) {
      this.playbookService.deletePlaybook(id).subscribe(() => {
        this.loadPlaybooks(); // Refresh the list
      });
    }
  }
}
