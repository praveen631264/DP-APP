
import { Component, Inject } from '@angular/core';
import { FormBuilder, FormGroup, FormArray, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

// Angular Material Modules
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { TextFieldModule } from '@angular/cdk/text-field';

import { Playbook } from '../services/playbook.service';

// Define the structure for each step's configuration
interface StepField {
  name: string;
  type: 'text' | 'textarea';
  label: string;
  defaultValue?: any;
}

interface StepConfig {
  [key: string]: {
    name: string;
    fields: StepField[];
  };
}

// Configuration object for all available step types and their fields
const STEP_CONFIG: StepConfig = {
  llm_prompt_step: {
    name: 'LLM Prompt',
    fields: [
      { name: 'prompt', type: 'textarea', label: 'Prompt Template', defaultValue: '' },
      { name: 'output_variable', type: 'text', label: 'Output Variable Name', defaultValue: 'llm_output' }
    ]
  },
  notification_step: {
    name: 'Email Notification',
    fields: [
      { name: 'recipients', type: 'text', label: 'Recipients (comma-separated)', defaultValue: '' },
      { name: 'subject', type: 'text', label: 'Subject', defaultValue: '' },
      { name: 'body', type: 'textarea', label: 'Body Template', defaultValue: '' }
    ]
  },
  search_step: {
    name: 'Search',
    fields: [
      { name: 'query', type: 'text', label: 'Search Query Template', defaultValue: '' },
      { name: 'output_variable', type: 'text', label: 'Output Variable Name', defaultValue: 'search_results' }
    ]
  },
  conditional_step: {
      name: 'Conditional (If/Else)',
      fields: [
          { name: 'condition', type: 'textarea', label: 'Condition (e.g., {{variable}} == "value")', defaultValue: ''}
      ]
  },
  for_each_step: {
      name: 'For Each Loop',
      fields: [
          { name: 'items', type: 'text', label: 'Items Variable (e.g., {{search_results}})', defaultValue: ''},
          { name: 'loop_variable', type: 'text', label: 'Loop Variable Name', defaultValue: 'item'}
      ]
  },
  update_document_step: {
      name: 'Update Document',
      fields: [
          { name: 'field', type: 'text', label: 'Field to Update', defaultValue: '' },
          { name: 'value', type: 'textarea', label: 'Value Template', defaultValue: ''}
      ]
  },
  api_call_step: {
    name: 'API Call',
    fields: [
        { name: 'url', type: 'text', label: 'URL Template', defaultValue: '' },
        { name: 'method', type: 'text', label: 'Method (GET, POST, etc.)', defaultValue: 'GET' },
        { name: 'payload', type: 'textarea', label: 'Payload (JSON Template)', defaultValue: '{}' },
        { name: 'output_variable', type: 'text', label: 'Output Variable Name', defaultValue: 'api_response' }
    ]
  }
};

@Component({
  selector: 'app-playbook-editor',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDividerModule,
    MatExpansionModule,
    TextFieldModule
  ],
  templateUrl: './playbook-editor.component.html',
  styleUrls: ['./playbook-editor.component.scss']
})
export class PlaybookEditorComponent {
  playbookForm: FormGroup;
  stepConfig = STEP_CONFIG;
  availableStepTypes = Object.keys(this.stepConfig);

  constructor(
    public dialogRef: MatDialogRef<PlaybookEditorComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { playbook: Playbook },
    private fb: FormBuilder
  ) {
    // Initialize the main form group
    this.playbookForm = this.fb.group({
      name: [data.playbook?.name || '', Validators.required],
      category_name: [data.playbook?.category_name || '', Validators.required],
      steps: this.fb.array([])
    });

    // If we are editing a playbook, populate the steps array
    if (data.playbook?.steps) {
      data.playbook.steps.forEach(step => {
        this.steps.push(this.createStepGroup(step.type, step));
      });
    }
  }

  // Getter for easy access to the steps FormArray
  get steps(): FormArray {
    return this.playbookForm.get('steps') as FormArray;
  }

  createStepGroup(stepType: string, stepData: any = null): FormGroup {
    const config = this.stepConfig[stepType];
    const group: { [key: string]: any; } = {
      name: [stepData?.name || 'New Step', Validators.required],
      type: [stepType, Validators.required]
    };

    if (config) {
      config.fields.forEach(field => {
        group[field.name] = [stepData?.[field.name] ?? field.defaultValue];
      });
    } else {
        if(stepData) {
            Object.keys(stepData).forEach(key => {
                if(!group[key]) {
                    group[key] = [stepData[key]];
                }
            })
        }
    }

    return this.fb.group(group);
  }

  addStep(stepType: string): void {
    if (!stepType) return;
    this.steps.push(this.createStepGroup(stepType));
  }

  removeStep(index: number): void {
    this.steps.removeAt(index);
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  onSave(): void {
    if (this.playbookForm.valid) {
      this.dialogRef.close(this.playbookForm.value);
    }
  }
}
