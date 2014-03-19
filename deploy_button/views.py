from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from deploy_button.tasks import deploy as deploy_task


@staff_member_required
def deploy(request):
    result = deploy_task.delay()
    return HttpResponse(result.task_id)

