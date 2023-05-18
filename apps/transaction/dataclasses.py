from dataclasses import dataclass
from typing import Tuple

from _decimal import Decimal

from apps.account.models import User

# TODO CT: All of these can actually become their own models


@dataclass
class BaseDataTuple:
    _data_type = object
    _data_tuple: Tuple[_data_type] = ()

    def __iter__(self):
        self.iter_index = 0
        return self

    def __next__(self):
        if self.iter_index > len(self._data_tuple) - 1:
            raise StopIteration

        next_item = self._data_tuple[self.iter_index]

        self.iter_index += 1
        return next_item

    def __len__(self):
        return len(self._data_tuple)

    def __getitem__(self, item):
        return self._data_tuple[item]

    def add_item(self, item: _data_type):
        self._data_tuple += (item,)

    def first(self):
        try:
            return self._data_tuple[0]
        except IndexError:
            return None

    def exists(self):
        return len(self._data_tuple) > 0

    def filter(self, **kwargs):
        ret = self._data_tuple

        for uncleaned_kwarg in kwargs:
            kwarg_list = uncleaned_kwarg.split("__")
            kwarg = kwarg_list[0]

            if len(kwarg_list) == 1:
                # If len is 1, that means, that no special operation was specified, hence check for equality
                ret = tuple(filter(lambda i: getattr(i, kwarg) == kwargs[kwarg], ret))

            elif len(kwarg_list) == 2:
                operation = kwarg_list[1]

                match operation:
                    case "not":
                        ret = tuple(
                            filter(
                                lambda i: getattr(i, kwarg)
                                != kwargs[f"{kwarg}__{operation}"],
                                ret,
                            )
                        )

                    # If an exact match is not confirmed, this last case will be used if provided
                    case _:
                        raise ValueError(
                            f"operation could not be resolved! {operation=}"
                        )
            else:
                raise ValueError(f"wtf\n{kwarg_list=}")

        return DebtTuple(ret)

    def get(self, **kwargs) -> _data_type:
        filtered_data_tuple = self.filter(**kwargs)

        if len(filtered_data_tuple) != 1:
            raise ValueError(
                f".get() did not return 1 object, it returned {len(filtered_data_tuple)}!"
            )

        return filtered_data_tuple[0]

    def update_data(
        self, item: _data_type, data_tuple_without_updated_item, **kwargs
    ) -> _data_type:
        for uncleaned_kwarg in kwargs:
            kwarg_list = uncleaned_kwarg.split("__")
            kwarg = kwarg_list[0]

            if len(kwarg_list) == 1:
                setattr(item, kwarg, kwargs[kwarg])
            elif len(kwarg_list) == 2:
                operation = kwarg_list[1]
                match operation:
                    case "add":
                        old_value = getattr(item, kwarg)
                        new_value = kwargs[f"{kwarg}__{operation}"]
                        setattr(item, kwarg, old_value + new_value)

                    case "subtract":
                        old_value = getattr(item, kwarg)
                        new_value = kwargs[f"{kwarg}__{operation}"]
                        setattr(item, kwarg, old_value - new_value)

                    # If an exact match is not confirmed, this last case will be used if provided
                    case _:
                        raise ValueError(
                            f"operation could not be resolved! {operation=}"
                        )
            else:
                raise ValueError(f"wtf\n{kwarg_list=}")

        self._data_tuple = data_tuple_without_updated_item._data_tuple
        self.add_item(item)

        return item

    def print_items(self):
        for item in self._data_tuple:
            print(item)


@dataclass
class Debt:
    debitor: User
    creditor: User
    deb_cred: Tuple[User, User]
    amount_owed: Decimal

    def __init__(self, debitor: User, creditor: User, amount_owed: Decimal):
        if debitor == creditor:
            raise ValueError(f"debitor == creditor ({debitor})")
        if amount_owed == 0:
            raise ValueError(
                "The amount_owed was going to be 0. This does not make sense, there should be no debt created then"
            )

        # self.id = uuid4()
        self.debitor = debitor
        self.creditor = creditor
        self.amount_owed = amount_owed

        self.deb_cred = (debitor, creditor)


@dataclass
class DebtTuple(BaseDataTuple):
    _data_type = Debt

    def update_debt(self, item: Debt, **kwargs) -> Debt:
        data_tuple_without_updated_item = self.filter(deb_cred__not=item.deb_cred)
        return self.update_data(item, data_tuple_without_updated_item, **kwargs)


@dataclass
class MoneyFlow:
    user: User
    outgoing: Decimal = Decimal(0)
    incoming: Decimal = Decimal(0)

    def optimise_flows(self):
        if self.outgoing > self.incoming:
            self.outgoing = self.outgoing - self.incoming
            self.incoming = Decimal(0)
        else:
            self.incoming = self.incoming - self.outgoing
            self.outgoing = Decimal(0)


@dataclass
class MoneyFlowTuple(BaseDataTuple):
    _data_type = MoneyFlow

    def update_debt(self, item: MoneyFlow, **kwargs) -> MoneyFlow:
        data_tuple_without_updated_item = self.filter(user__not=item.user)
        return self.update_data(item, data_tuple_without_updated_item, **kwargs)
