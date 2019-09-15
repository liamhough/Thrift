import requests
import json
import numpy as np
import operator
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Profile
from rest_framework.response import Response
import json


def get_customer_average_spending(customer_id):
    response = requests.get(
        "https://api.td-davinci.com/api/customers/" + customer_id + "/transactions",
        headers={
            "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJDQlAiLCJ0ZWFtX2lkIjoiYTQ4MjM5ODMtZTExOS0zMDIxLWI1ZDMtZDM3ZDZmM2NjNTgyIiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJhcHBfaWQiOiIwOGRmYmFhMC03ZWI5LTQxM2ItOGQ0NS0wMGE0NmY4ZTAyYzAifQ.JKMjg-_quhsyB7c0ICdN1u-8yG44wzNlFpNYpCjoR6o"
        },
    )
    response_data = response.json()

    data = json.loads(response.text)

    results = data["result"]

    results.sort(key=lambda r: r["originationDateTime"])

    monthly_periods = [i for i in range(27, 32)]
    amounting_periods = list(map(lambda x: float(len(results) / x), monthly_periods))
    minimization_factor = list(map(lambda x: x - int(x), amounting_periods))
    result_index = minimization_factor.index(min(minimization_factor))
    period = monthly_periods[result_index]
    iteration_factor = int(amounting_periods[result_index])
    expenditure_mappings = {
        "Food and Dining": -1.0,
        "Shopping": -1.0,
        "Bills and Utilities": -1.0,
        "Transfer": -1.0,
        "Auto and Transport": -1.0,
        "Income": 1.0,
        "Home": -1.0,
        "Entertainment": -1.0,
        "Taxes": -1.0,
        "Mortgage and Rent": -1.0,
        "Fees and Charges": -1.0,
        "Health and Fitness": -1.0,
        "Travel": -1.0,
        "unknown": -1.0,
    }

    categories = {}
    totals = []
    counter = 0
    print(iteration_factor)

    for i in range(iteration_factor):
        total = 0
        for x in range(period):
            try:
                category = results[counter]["categoryTags"][0]

            except:
                category = "unknown"

            if category == "Income":
                amount = 0
            else:
                amount = results[counter]["currencyAmount"]
            total += float(abs(amount))
            try:
                categories[category]["Spendings"][str(i)].append(float(abs(amount)))
            except KeyError:
                period_dict = {}
                for z in range(iteration_factor):
                    period_dict[str(z)] = []
                categories[category] = {"Spendings": period_dict}
                categories[category]["Spendings"][str(i)].append(float(abs(amount)))
            counter += 1

        totals.append(total)

    #
    #    print(counter)
    #    print(categories)
    #    print(totals)

    return categories, totals


def get_final_categorization(customer_id):
    customer_categories, totals = get_customer_average_spending(customer_id)
    categories = customer_categories.keys()
    modified_data_category = {}

    for key in categories:
        modified_data_category[key] = {"period_totals": []}
        period_list = customer_categories[key]["Spendings"]
        period_means = []
        for period in period_list.keys():
            modified_data_category[key]["period_totals"].append(
                round(sum(period_list[period]), 2)
            )
            try:
                period_mean = round(
                    float(sum(period_list[period]) / len(period_list[period])), 2
                )
                period_means.append(period_mean)
            except ZeroDivisionError:
                period_means.append(0)
        try:
            modified_data_category[key]["average_payment"] = round(
                float(sum(period_means) / len(period_means)), 2
            )
        except ZeroDivisionError:
            modified_data_category[key]["average_payment"] = 0

        period_totals = np.array(modified_data_category[key]["period_totals"])
        modified_data_category[key]["monthly_average"] = np.mean(period_totals)

        array_totals = np.array(totals)
        average_percentage = float(sum((period_totals / array_totals)) / len(totals))

        modified_data_category[key]["average_percentage"] = round(
            100 * average_percentage, 2
        )

        final_category = {}

        for i in modified_data_category.keys():

            if i != "Income":
                final_category[i] = modified_data_category[i]
            else:
                continue
    return final_category


def get_percentages(final_category):
    keys = []
    percentages = []
    for i in final_category.keys():
        keys.append(i)
        percentages.append(final_category[i]["average_percentage"])

    return [keys, percentages]


# print(get_percentages(final_cat))
def get_spending_trends(final_category):

    plot_list = []
    for i in list(final_category.keys())[:2]:
        plot_set = {}
        months = [i + 1 for i in range(len(final_category[i]["period_totals"]))]
        data = final_category[i]["period_totals"]
        plot_set["title"] = i
        plot_set["months"] = months
        plot_set["data"] = data

        plot_list.append(plot_set)

    return plot_list


@api_view(["POST"])
@csrf_exempt
def create_customer_profile(request):
    if request.method == "POST":
        data = request.data
        user = User.objects.get(email=data["email_address"])
        customer_id = data["customer_id"]
        prof = Profile(user=user, customer_id=customer_id)
        prof.save()
        user.save()
    return Response({"message": "failed to handle Requeust"})


@api_view(["POST"])
@csrf_exempt
def create_priority_map(request):
    if request.method == "POST":
        data = request.data
        user = User.objects.get(email=data["email_address"])
        priority_mapping = str(data["priority_map"])
        user.profile.priority_map = priority_mapping
        user.save()
    return Response({"message": "failed to handle Requeust"})


@api_view(["POST"])
@csrf_exempt
def get_priority_categories(request):
    if request.method == "POST":
        data = request.data
        user = User.objects.get(email=data["email_address"])
        customer_id = user.profile.customer_id
        categories = get_final_categorization(customer_id)

        cats = list(categories.keys())
    return Response({"categories": cats})


@api_view(["POST"])
@csrf_exempt
def get_trend_data(request):
    if request.method == "POST":
        data = request.data
        user = User.objects.get(email=data["email_address"])
        cus_id = user.profile.customer_id
        categories = get_final_categorization(cus_id)
        percentage_data = get_percentages(categories)
        trends = get_spending_trends(categories)

        return Response({"percentages": percentage_data, "trends": trends})

    return Response({"error": "Failed request"})


@api_view(["POST"])
@csrf_exempt
def get_customer_info(request):
    if request.method == "POST":
        data = request.data
        print("------------", data)
        user = User.objects.get(email=data["email_address"])
        customer_id = user.profile.customer_id
        response = requests.get(
            "https://api.td-davinci.com/api/customers/" + customer_id,
            headers={
                "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJDQlAiLCJ0ZWFtX2lkIjoiYTQ4MjM5ODMtZTExOS0zMDIxLWI1ZDMtZDM3ZDZmM2NjNTgyIiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJhcHBfaWQiOiIwOGRmYmFhMC03ZWI5LTQxM2ItOGQ0NS0wMGE0NmY4ZTAyYzAifQ.JKMjg-_quhsyB7c0ICdN1u-8yG44wzNlFpNYpCjoR6o"
            },
        )
        data = json.loads(response.text)

    return Response(data)


class Savings(object):
    def __init__(self, title, avg_spending, prioritization):
        self.title = title
        self.avg_spending = avg_spending
        self.prioritization = prioritization
        self.priority_ratio = float(avg_spending / prioritization)

    def get_title(self):
        return self.title

    def get_spending(self):
        return float(self.avg_spending)

    def get_prioritization(self):
        return float(self.prioritization)

    def get_priority_ratio(self):
        return float(self.avg_spending / self.prioritization)

    def __str__(self):
        return self.title


def make_savings_plan(final_categories, set_amount, periods):

    priority_mapping = {
        "Food and Dining": 4,
        "Shopping": 4,
        "Bills and Utilities": 4,
        "Transfer": 4,
        "Auto and Transport": 4,
        "Income": 4,
        "Home": 4,
        "Entertainment": 4,
        "Taxes": 4,
        "Mortgage and Rent": 4,
        "Fees and Charges": 4,
        "Health and Fitness": 4,
        "Travel": 4,
        "unknown": 4,
    }

    saving_per_period = float(set_amount)
    savings = 0
    saving_objects = []
    for i in final_categories.keys():
        title = i
        avg_spending = final_categories[i]["average_payment"]
        priority = priority_mapping[i]
        saving_object = Savings(title, avg_spending, priority)
        saving_objects.append(saving_object)

    optimized_saving_options = sorted(
        saving_objects, key=operator.attrgetter("priority_ratio")
    )

    index = 0

    saving_plan = {}
    saved_amount = 0

    while index < len(optimized_saving_options):
        current_saving_option = final_categories[str(optimized_saving_options[index])]
        per_month = current_saving_option["monthly_average"]
        avg_payment = current_saving_option["average_payment"]
        saved_amount += per_month

        if float((0.5 * saved_amount) / saving_per_period) < 1.0:

            try:
                payment_per_month = int(0.5 * int((per_month / (avg_payment))))
                amount_per_month = round(payment_per_month * avg_payment, 2)
                saving_plan[str(optimized_saving_options[index])] = {
                    "payment_no": payment_per_month,
                    "amount": amount_per_month,
                }
                index += 1
            except ValueError:
                continue

        else:
            break

    if saving_plan == {}:
        return "Funds are already sufficient to support the given amount"
    if saved_amount < saving_per_period:
        return "Saving amount not possible given current account status"

    return saving_plan


@api_view(["POST"])
@csrf_exempt
def get_saving_plan(request):
    if request.method == "POST":
        data = request.data
        user = User.objects.get(email=data["email_address"])
        amount = int(data["savings"])
        periods = int(data["periods"])
        customer_id = user.profile.customer_id
        categories = get_final_categorization(customer_id)
        res = make_savings_plan(categories, amount, periods)
        return Response({"cats": list(res.keys()), "vals": list(res.values())})
    return Response({"None": "negatory m8"})

